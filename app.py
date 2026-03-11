import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request

app = Flask(__name__)

def hash_password(password):
    """SHA-256 hash — replace with bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def home():
    return jsonify({"message": "Flask API running on Render"})

@app.route("/api/db-check")
def db_check():
    return jsonify({"status": "Pending", "message": "Database not configured yet"}), 503

@app.post("/api/login")
def authenticate():
    data = request.get_json(silent=True) or request.form or {}
    username = (data.get("username") or data.get("login_id") or "").strip()
    password = (data.get("password") or data.get("login_pwd") or "").strip()

    if not username or not password:
        return jsonify({"status": "Error", "message": "username and password are required"}), 400

    # TODO: query database once configured
    return jsonify({"status": "Error", "message": "Database not configured yet"}), 503

@app.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or request.form or {}
    full_name = (data.get("full_name") or "").strip()
    username  = (data.get("username")  or "").strip()
    email     = (data.get("email")     or "").strip()
    password  = (data.get("password")  or "").strip()

    missing = [f for f, v in [("full_name", full_name), ("username", username),
                               ("email", email), ("password", password)] if not v]
    if missing:
        return jsonify({"status": "Error", "message": f"Missing required fields: {', '.join(missing)}"}), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"status": "Error", "message": "Invalid email format"}), 400

    if len(password) < 6:
        return jsonify({"status": "Error", "message": "Password must be at least 6 characters"}), 400

    # TODO: insert into database once configured
    return jsonify({"status": "Error", "message": "Database not configured yet"}), 503

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
