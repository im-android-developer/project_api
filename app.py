import os

from flask import Flask, jsonify, request

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

@app.post("/api/login")
def authenticate():
    data = request.get_json(silent=True) or request.form or {}
    login_id = data.get("login_id")
    login_pwd = data.get("login_pwd")

    if not login_id or not login_pwd:
        return jsonify({
            "status": "Error",
            "message": "login_id and login_pwd are required"
        }), 400

    # Hardcoded credentials — replace with DB lookup later
    VALID_USERS = {
        "demo": "demo123"
    }

    if VALID_USERS.get(login_id) == login_pwd:
        return jsonify({"status": "OK"}), 200

    return jsonify({
        "status": "Error",
        "message": "Invalid login_id or login_pwd"
    }), 401

@app.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or request.form or {}

    full_name = (data.get("full_name") or "").strip()
    username  = (data.get("username")  or "").strip()
    email     = (data.get("email")     or "").strip()
    password  = (data.get("password")  or "").strip()

    # Validate required fields
    missing = [f for f, v in [("full_name", full_name), ("username", username),
                               ("email", email), ("password", password)] if not v]
    if missing:
        return jsonify({
            "status": "Error",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    # Basic email format check
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "status": "Error",
            "message": "Invalid email format"
        }), 400

    # Password length check
    if len(password) < 6:
        return jsonify({
            "status": "Error",
            "message": "Password must be at least 6 characters"
        }), 400

    # TODO: Store user in database
    return jsonify({"status": "OK"}), 201


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
