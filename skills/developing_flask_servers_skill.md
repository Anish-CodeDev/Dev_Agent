--- 
name: flask-server-development
description: >
  Builds and configures Python web servers using the Flask framework. Use this skill whenever a user requests to "create a flask app", "set up a web server in python", "build a REST API", or "make a backend with flask". It handles application setup, route definition, request parsing, and JSON response generation.
compatibility:
  runtime: Python 3.8+
  dependencies: flask
  env_vars: FLASK_APP, FLASK_ENV (optional)
---

# Develop Flask Servers

This skill enables the agent to design and implement lightweight web services and APIs using Flask, ensuring proper project structure and error handling.

---

## Prerequisites

- Python must be installed in the environment.
- Flask must be installed via pip.

```bash
pip install flask
```

---

## Core Concepts

- **Application Instance:** The central registry for configurations, URL rules, and setup.
- **Routing:** Mapping URLs to Python functions using the `@app.route()` decorator.
- **Request Context:** Accessing incoming data via `flask.request` (JSON, forms, args).
- **JSON Responses:** Returning dictionaries or lists that Flask automatically converts to JSON with `flask.jsonify` or direct returns in Flask 2.0+.

---

## Step-by-Step Instructions

1. **Initialize the Project** — Create a new directory and a main application file (usually `app.py`).
2. **Import and Instantiate** — Import the Flask class and create the `app` object.
3. **Define Endpoints** — Use decorators to define paths and allowed HTTP methods (GET, POST, etc.).
4. **Handle Data** — For POST requests, use `request.get_json()` to extract payload data.
5. **Return Responses** — Return data and an appropriate HTTP status code (e.g., 200 for OK, 201 for Created).
6. **Run the Server** — Include a protection block to run the app in debug mode during development.

---

## Full Example

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# A simple GET endpoint
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "online", "version": "1.0.0"}), 200

# A POST endpoint that processes data
@app.route('/api/echo', methods=['POST'])
def echo_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    return jsonify({"received": data}), 201

if __name__ == '__main__':
    # Run server on port 5000 with debug enabled
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

## Error Handling & Edge Cases

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Address already in use` | Another process is on port 5000 | Change `port=5001` in `app.run()` or kill the other process |
| `405 Method Not Allowed` | Calling endpoint with wrong HTTP verb | Add the method to the `@app.route(..., methods=['GET', 'POST'])` list |
| `TypeError: ... is not JSON serializable` | Returning a non-serializable object (like a class instance) | Convert the object to a dictionary or list before returning |

---

## Output Format

The primary output should be a complete `app.py` file containing the server logic, followed by a command-line instruction on how to run it (e.g., `python app.py`).

---

## Test Cases

### Test Case 1 — Happy Path
**Prompt:** "Create a flask app with a root route that returns 'Welcome to my API'."
**Expected behaviour:** Agent generates an `app.py` with `@app.route('/')` returning the string and includes `app.run()`.
**Pass criteria:** The code is valid Python and uses the Flask library correctly.

### Test Case 2 — JSON API
**Prompt:** "Build a Flask server with a POST endpoint at /multiply that takes two numbers and returns their product."
**Expected behaviour:** Agent implements an endpoint that extracts JSON, performs multiplication, and returns a JSON response.
**Pass criteria:** Response includes `jsonify` or a dict and correctly handles the POST method.

### Test Case 3 — Error Recovery
**Prompt:** "My flask server keeps crashing with 'ModuleNotFoundError: No module named flask'."
**Expected behaviour:** Agent identifies that the dependency is missing and instructs the user to run `pip install flask`.
**Pass criteria:** The agent provides the specific installation command rather than just stating the error.
