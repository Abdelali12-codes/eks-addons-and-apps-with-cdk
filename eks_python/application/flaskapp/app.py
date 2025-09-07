from flask import Flask

app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return "Welcome to the Home Page!"

# About route
@app.route("/about")
def about():
    return "This is the About Page."

# Dynamic route with a parameter
@app.route("/hello/<name>")
def hello(name):
    return f"Hello, {name.capitalize()}!"

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
