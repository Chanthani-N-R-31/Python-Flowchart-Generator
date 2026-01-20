📊 LogicFlow: Python Code & Flowchart Generator
LogicFlow is a powerful web-based utility designed to help developers and students visualize programming logic. It transforms text-based prompts into both functional Python code and structured visual flowcharts simultaneously.

🚀 The Vision
The goal of this project was to create a seamless transition between "thinking in logic" and "writing in code." By providing a visual representation of the control flow alongside the syntax, users can debug logic errors before they even run the script.

🛠️ Key Features
Logic Visualization: Automatically converts complex nested loops and conditional statements into clean, readable flowcharts.

Integrated Code Console: A dedicated code viewer designed for high readability with syntax-aware formatting.

Interactive Diagram Canvas: * Zoom & Pan: Custom-built JavaScript controls to handle large-scale logic maps.

SVG Rendering: High-resolution flowchart rendering using Mermaid.js.

Secure Access: Integrated Google OAuth 2.0 system for personalized user sessions and profile management.

Context Persistence: Seamlessly toggle between the code view and the flowchart view without losing your current prompt.

🏗️ System Architecture
The application follows a classic Model-View-Controller (MVC) pattern:

Frontend: Built with HTML5, CSS3, and Vanilla JavaScript. It uses a MutationObserver to detect when diagrams are rendered to apply dynamic scaling.

Backend: A Flask (Python) server manages the routing, session handling, and API communication.

Diagram Engine: Leverages the Mermaid.js library to parse text-based graph definitions into interactive SVG elements.

💻 Technical Setup
Prerequisites
Python 3.x

Google Cloud Console credentials (for OAuth)

API Key for the LLM engine

Installation
Clone the repository

Bash

git clone https://github.com/your-username/logicflow-generator.git
Install requirements

Bash

pip install -r requirements.txt
Environment Variables Create a .env file in the root directory:

Code snippet

FLASK_APP=app.py
SECRET_KEY=your_secret
GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret
API_KEY=your_llm_api_key
Launch

Bash

flask run
