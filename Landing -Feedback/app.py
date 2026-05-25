from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("products.html")

@app.route("/api/products")
def get_products():
    file_path = os.path.join("static", "products.json")
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
