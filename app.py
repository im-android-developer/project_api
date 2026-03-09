import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# Dummy credentials for testing login flow.
DUMMY_USERS = {
    "demo": "demo123",
    "testuser": "test@123"
}

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

    # Accept both new and legacy payload keys.
    username = (data.get("username") or data.get("login_id") or "").strip()
    password = (data.get("password") or data.get("login_pwd") or "").strip()

    if not username or not password:
        return jsonify({
            "status": "Error",
            "message": "username and password are required"
        }), 400

    if DUMMY_USERS.get(username) == password:
        return jsonify({"status": "OK"}), 200

    return jsonify({
        "status": "Error",
        "message": "Invalid username or password"
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
