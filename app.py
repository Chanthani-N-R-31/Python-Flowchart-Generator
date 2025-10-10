import os
import secrets
import ast
import traceback
from flask import Flask, redirect, render_template, url_for, session, request
from flask_dance.contrib.google import make_google_blueprint, google
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from dotenv import load_dotenv
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

# --- Load .env file ---
load_dotenv()

# --- Load Environment Variables ---
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# --- Firebase Setup ---
try:
    if not FIREBASE_KEY_PATH:
        raise ValueError("FIREBASE_KEY_PATH environment variable not set.")
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization error: {e}")
    db = None

# --- Google OAuth Setup ---
app.config["GOOGLE_OAUTH_CLIENT_ID"] = GOOGLE_OAUTH_CLIENT_ID
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = GOOGLE_OAUTH_CLIENT_SECRET

blueprint = make_google_blueprint(
    client_id=app.config["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=app.config["GOOGLE_OAUTH_CLIENT_SECRET"],
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to="index"
)
app.register_blueprint(blueprint, url_prefix="/login")

# --- Gemini Setup ---
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)


# ==============================================================================
# HELPER FUNCTION TO SYNC GOOGLE USER WITH FIREBASE
# ==============================================================================
def sync_firebase_user(google_user_info):
    if not db or not google_user_info or 'id' not in google_user_info:
        return google_user_info
    uid = google_user_info['id']
    email = google_user_info.get('email')
    name = google_user_info.get('name')
    user_ref = db.collection('users').document(uid)
    try:
        user_doc = user_ref.get()
        if user_doc.exists:
            return user_doc.to_dict()
        else:
            user_data = {'name': name, 'email': email, 'uid': uid}
            user_ref.set(user_data)
            return user_data
    except Exception as e:
        print(f"Error interacting with Firestore: {e}")
        return google_user_info


# ==============================================================================
# ADVANCED FLOWCHART PARSER
# ==============================================================================
def generate_mermaid_flowchart(code):
    try:
        nodes, edges = parse_code_to_ast(code)
        mermaid_string = "graph TD\n"
        for node_id, data in nodes.items():
            label = data['label'].replace('"', '&quot;')
            shape_start, shape_end = data['shape']
            mermaid_string += f'    {node_id}{shape_start}"{label}"{shape_end}\n'
        for src, tgt, label in edges:
            if src and tgt: # Ensure both source and target nodes exist
                if label:
                    mermaid_string += f'    {src} -->|{label}| {tgt}\n'
                else:
                    mermaid_string += f'    {src} --> {tgt}\n'
        return mermaid_string
    except Exception as e:
        print(f"Error parsing code for flowchart: {e}\n{traceback.format_exc()}")
        return "graph TD\n    A[Error: Could not parse code]"

def parse_code_to_ast(code):
    tree = ast.parse(code)
    nodes, edges, functions, node_counter = {}, [], {}, 0
    def get_node_id():
        nonlocal node_counter
        node_id = f"N{node_counter}"; node_counter += 1
        return node_id
    def add_node(label, shape):
        node_id = get_node_id()
        nodes[node_id] = {"label": label, "shape": shape}
        return node_id
    def visit(node, parent_id, loop_start_id=None, loop_exit_id=None):
        node_type = type(node)

        if node_type in (ast.Assign, ast.AugAssign):
            label = ast.unparse(node).strip()
            current_id = add_node(label, ("[/", "/]"))
            edges.append((parent_id, current_id, ""))
            return current_id
        
        elif node_type is ast.Expr:
            label = ast.unparse(node).strip()
            shape = ("[", "]")
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                func_id = node.value.func.id
                if func_id in ['input', 'print']: shape = ("[/", "/]")
                elif func_id in functions:
                    current_id = add_node(label, shape)
                    edges.append((parent_id, current_id, ""))
                    last_node_in_func = current_id
                    for func_stmt in functions[func_id]["body"]:
                        last_node_in_func = visit(func_stmt, last_node_in_func, loop_start_id, loop_exit_id)
                    return last_node_in_func
            current_id = add_node(label, shape)
            edges.append((parent_id, current_id, ""))
            return current_id

        elif node_type is ast.Return:
            label = ast.unparse(node).strip()
            current_id = add_node(label, ("(", ")"))
            edges.append((parent_id, current_id, ""))
            return None # Terminal node for this path

        elif node_type is ast.If:
            label = f"if {ast.unparse(node.test).strip()}"
            cond_id = add_node(label, ("{", "}"))
            edges.append((parent_id, cond_id, ""))
            
            true_end = cond_id
            for child in node.body:
                if true_end: true_end = visit(child, true_end, loop_start_id, loop_exit_id)
            
            false_end = cond_id
            if node.orelse:
                for child in node.orelse:
                    if false_end: false_end = visit(child, false_end, loop_start_id, loop_exit_id)

            # If both branches terminate (e.g., return), there's no merge
            if not true_end and not false_end: return None
            
            merge_id = add_node(" ", ("((", "))"))
            if true_end: edges.append((true_end, merge_id, "Yes"))
            if false_end: edges.append((false_end, merge_id, "No"))

            # Handle case where one branch is empty
            if not node.body: edges.append((cond_id, merge_id, "Yes"))
            if not node.orelse: edges.append((cond_id, merge_id, "No"))
            
            return merge_id
        
        elif node_type in (ast.For, ast.While):
            loop_type = "For" if node_type is ast.For else "While"
            condition = ast.unparse(node.target if node_type is ast.For else node.test).strip()
            label = f"{loop_type} {condition}"
            loop_id = add_node(label, ("{{", "}}"))
            edges.append((parent_id, loop_id, ""))
            
            after_loop_id = add_node(" ", ("((", "))"))
            body_end = loop_id
            for child in node.body:
                if body_end: body_end = visit(child, body_end, loop_id, after_loop_id)

            if body_end: edges.append((body_end, loop_id, "Loop"))
            edges.append((loop_id, after_loop_id, "End Loop"))
            return after_loop_id

        elif node_type is ast.Break:
            if loop_exit_id: edges.append((parent_id, loop_exit_id, "break"))
            return None # Terminal node
        
        elif node_type is ast.Continue:
            if loop_start_id: edges.append((parent_id, loop_start_id, "continue"))
            return None # Terminal node
        
        last_id = parent_id
        for child in ast.iter_child_nodes(node):
            if last_id: last_id = visit(child, last_id, loop_start_id, loop_exit_id)
        return last_id
    
    # --- Main Parsing Logic ---
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = { "body": node.body, "args": [arg.arg for arg in node.args.args] }
            
    start_id = add_node("Start", ("((", "))"))
    last_node_id = start_id
    
    main_body = [n for n in tree.body if not isinstance(n, ast.FunctionDef)]
    
    if not main_body and functions:
        first_func_name = list(functions.keys())[0]
        func_def_label = f"def {first_func_name}(...)"
        func_def_id = add_node(func_def_label, ("[[", "]]"))
        edges.append((start_id, func_def_id, ""))
        last_node_id = func_def_id
        for node in functions[first_func_name]["body"]:
            if last_node_id: last_node_id = visit(node, last_node_id)
    else:
        for node in main_body:
            if last_node_id: last_node_id = visit(node, last_node_id)
        
    end_id = add_node("End", ("((", "))"))
    if last_node_id: edges.append((last_node_id, end_id, ""))
    
    return nodes, edges


# ==============================================================================
# --- Routes ---
# ==============================================================================
@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("login"))
    try:
        resp = google.get("/oauth2/v2/userinfo")
        user_info_from_google = resp.json() if resp.ok else {}
        user = sync_firebase_user(user_info_from_google)
        session['user'] = user
        return render_template("index.html", user=user, response=None)
    except TokenExpiredError:
        session.clear()
        return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/generate", methods=["POST"])
def generate():
    user = session.get('user')
    if not user:
        return redirect(url_for("login"))

    prompt = request.form.get("prompt")
    action = request.form.get("action")
    code_from_form = request.form.get("code")

    if not prompt:
        return render_template("index.html", user=user, response="⚠️ Please enter a prompt.")

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")

        if action == "code":
            gemini_prompt = f"Write only the python code for the following task, without comments, explanation, or markdown. Task: {prompt}"
            response = model.generate_content(gemini_prompt)
            code = response.text.strip().replace("```python", "").replace("```", "") if response.text else "No code generated."
            return render_template("code.html", prompt=prompt, code=code, user=user)

        elif action == "flowchart":
            if code_from_form:
                code = code_from_form
            else:
                code_prompt = f"Write only the python code for the following task, without comments, explanation, or markdown. Task: {prompt}"
                code_response = model.generate_content(code_prompt)
                code = code_response.text.strip().replace("```python", "").replace("```", "") if code_response.text else "No code generated."
            
            flowchart = generate_mermaid_flowchart(code)

            return render_template("flowchart.html", prompt=prompt, code=code, flowchart=flowchart, user=user)

    except Exception as e:
        error_message = f"⚠️ An error occurred: {str(e)}"
        return render_template("index.html", user=user, response=error_message)
    
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

