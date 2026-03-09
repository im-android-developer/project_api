import os

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "Flask API running on Render"
    })

@app.route("/api/users")
def users():
    return jsonify({
        "users": ["Tarun", "Amit", "Rahul"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)