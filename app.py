import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from db import get_connection, execute_query
from psycopg2 import OperationalError, DatabaseError

app = Flask(__name__)

def hash_password(password):
    """SHA-256 hash — replace with bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def home():
    return jsonify({"message": "Flask API running on Render"})

@app.route("/api/checkconnection")
def check_connection():
    """Check PostgreSQL connectivity with specific error diagnosis."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "OK", "message": "Successfully connected"}), 200
    except OperationalError as e:
        err = str(e).lower()
        if "database_url" in err or "url" in err:
            problem = "DATABASE_URL environment variable is not set"
        elif "password authentication" in err or "role" in err:
            problem = "Access denied — wrong username or password"
        elif "does not exist" in err:
            problem = "Database does not exist — check DATABASE_URL"
        elif "could not connect" in err or "connection refused" in err:
            problem = "Cannot connect to host — wrong host/port or server is down"
        elif "name or service not known" in err or "could not translate" in err:
            problem = "Unknown host — check hostname in DATABASE_URL"
        else:
            problem = f"Connection error: {e}"
        return jsonify({"status": "Error", "problem": problem}), 500

@app.post("/api/login")
def authenticate():
    data     = request.get_json(silent=True) or request.form or {}
    user_id  = (data.get("user_id") or "").strip()
    password = (data.get("password") or "").strip()

    if not user_id or not password:
        return jsonify({"status": "Error", "message": "user_id and password are required"}), 400

    try:
        hashed = hash_password(password)
        rows = execute_query(
            "SELECT id, account_status FROM users WHERE (email = %s OR phone_number = %s) AND password = %s",
            (user_id, user_id, hashed),
            fetch=True
        )
        if rows:
            account_status = rows[0][1]
            if account_status == 'ACTIVE':
                return jsonify({"status": "OK", "message": "Login successful"}), 200
            elif account_status == 'BLOCKED':
                return jsonify({"status": "Error", "message": "Account is blocked"}), 403
            else:
                return jsonify({"status": "Error", "message": "Account is inactive"}), 403
        return jsonify({"status": "Error", "message": "Invalid credentials"}), 401
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500

@app.post("/api/signup")
def signup():
    data         = request.get_json(silent=True) or request.form or {}
    first_name   = (data.get("first_name")   or "").strip()
    last_name    = (data.get("last_name")    or "").strip()
    email        = (data.get("email")        or "").strip()
    username        = (data.get("username")        or "").strip()
    phone_number = (data.get("phone_number") or "").strip()
    password     = (data.get("password")     or "").strip()

    missing = [f for f, v in [("first_name", first_name), ("last_name", last_name),
                               ("email", email), ("username", username), ("phone_number", phone_number),
                               ("password", password)] if not v]
    if missing:
        return jsonify({"status": "Error", "message": f"Missing required fields: {', '.join(missing)}"}), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"status": "Error", "message": "Invalid email format"}), 400

    if len(phone_number) < 10:
        return jsonify({"status": "Error", "message": "Phone number must be at least 10 digits"}), 400

    if len(password) < 6:
        return jsonify({"status": "Error", "message": "Password must be at least 6 characters"}), 400

    try:
        hashed = hash_password(password)
        execute_query(
            "INSERT INTO users (first_name, last_name, email, username, phone_number, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, email, username, phone_number, hashed)
        )
        return jsonify({"status": "OK", "message": "User registered successfully"}), 201
    except DatabaseError as e:
        err = str(e).lower()
        if "unique" in err and "email" in err:
            return jsonify({"status": "Error", "message": "Email already registered"}), 409
        if "unique" in err and "phone" in err:
            return jsonify({"status": "Error", "message": "Phone number already registered"}), 409
        if "unique" in err and "username" in err:
            return jsonify({"status": "Error", "message": "Username already taken"}), 409
        return jsonify({"status": "Error", "message": "Database error"}), 500
    except OperationalError:
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
