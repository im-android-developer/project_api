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
    username = (data.get("username") or data.get("login_id") or "").strip()
    password = (data.get("password") or data.get("login_pwd") or "").strip()

    if not username or not password:
        return jsonify({"status": "Error", "message": "username and password are required"}), 400

    try:
        hashed = hash_password(password)
        rows = execute_query(
            "SELECT id FROM userbase WHERE (email = %s OR phone = %s) AND password = %s AND account_status = 'active'",
            (username, username, hashed),
            fetch=True
        )
        if rows:
            return jsonify({"status": "OK"}), 200
        return jsonify({"status": "Error", "message": "Invalid username or password"}), 401
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500

@app.post("/api/signup")
def signup():
    data      = request.get_json(silent=True) or request.form or {}
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

    try:
        hashed = hash_password(password)
        execute_query(
            "INSERT INTO userbase (full_name, email, password) VALUES (%s, %s, %s)",
            (full_name, email, hashed)
        )
        return jsonify({"status": "OK"}), 201
    except DatabaseError as e:
        err = str(e)
        if "unique" in err.lower() and "email" in err.lower():
            return jsonify({"status": "Error", "message": "Email already registered"}), 409
        return jsonify({"status": "Error", "message": "Database error"}), 500
    except OperationalError:
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
