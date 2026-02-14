from flask import Flask, render_template, request
app = Flask(__name__)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return f"Form submitted! Name: {request.form.get('name')}"
    return render_template("index.html")
if __name__ == "__main__":
    app.run()