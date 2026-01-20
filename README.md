# 📊 Python Flowchart & Code Generator

**LogicFlow** is a powerful web-based utility designed to help developers and students visualize programming logic. It transforms text-based prompts into both functional Python code and structured visual flowcharts simultaneously.

---

## 🚀 Overview
The goal of this project is to create a seamless transition between "thinking in logic" and "writing in code." By providing a visual representation of the control flow alongside the syntax, users can debug logic errors before they even run the script.

## ✨ Key Features
* **Logic Visualization:** Automatically converts complex nested loops and conditional statements into clean, readable flowcharts.
* **Integrated Code Console:** A dedicated code viewer designed for high readability with syntax-aware formatting.
* **Interactive Diagram Canvas:**
    * **Zoom & Pan:** Custom-built JavaScript controls to handle large-scale logic maps.
    * **SVG Rendering:** High-resolution flowchart rendering using **Mermaid.js**.
* **Secure Access:** Integrated Google OAuth 2.0 system for personalized user sessions.
* **Context Persistence:** Seamlessly toggle between the code view and the flowchart view without losing your current prompt.

## 🏗️ System Architecture
The application follows a classic **Model-View-Controller (MVC)** pattern:
* **Frontend:** Built with HTML5, CSS3, and Vanilla JavaScript. It uses a `MutationObserver` to detect when diagrams are rendered to apply dynamic scaling.
* **Backend:** A **Flask (Python)** server manages the routing, session handling, and API communication.
* **Diagram Engine:** Leverages the **Mermaid.js** library to parse text-based graph definitions into interactive SVG elements.

## 💻 Technical Setup

### Prerequisites
* Python 3.x
* Google Cloud Console credentials (for OAuth integration)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Chanthani-N-R-31/Python-Flowchart-Generator.git](https://github.com/Chanthani-N-R-31/Python-Flowchart-Generator.git)
    cd Python-Flowchart-Generator
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    flask run
    ```

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).

---
*Developed by [Chanthani N R](https://github.com/Chanthani-N-R-31)*
