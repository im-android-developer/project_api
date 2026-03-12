import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from db import get_connection, execute_query
from psycopg2 import OperationalError, DatabaseError

# SMTP Configuration (set these in Render environment variables)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "enfec.tarunbansal@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "vffbushrlfxoczmc")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "enfec.tarunbansal@gmail.com")

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


def send_email(to_email, subject, body):
    """Send email using SMTP configuration."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise ValueError("SMTP credentials not configured")

    msg = MIMEMultipart()
    msg['From'] = SMTP_FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())


@app.post("/api/sendotp")
def send_otp():
    """Send OTP to the specified email address."""
    email = request.headers.get("email", "").strip()
    otp = request.headers.get("otp", "").strip()

    if not email:
        return jsonify({"status": "Error", "message": "Email is required in header"}), 400
    if not otp:
        return jsonify({"status": "Error", "message": "OTP is required in header"}), 400

    try:
        subject = "Your OTP Verification Code"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>OTP Verification</h2>
            <p>Dear User,</p>
            <p>Your One-Time Password (OTP) for verification is:</p>
            <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; text-align: center;">
                <h1 style="color: #333; letter-spacing: 5px;">{otp}</h1>
            </div>
            <p>This OTP is valid for a limited time. Please do not share it with anyone.</p>
            <p>If you did not request this OTP, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Support Team</p>
        </body>
        </html>
        """
        send_email(email, subject, body)
        return jsonify({"status": "OK", "message": "OTP sent successfully"}), 200
    except ValueError as e:
        return jsonify({"status": "Error", "message": str(e), "reason": "SMTP credentials (SMTP_USERNAME or SMTP_PASSWORD) not configured in environment variables"}), 500
    except smtplib.SMTPAuthenticationError:
        return jsonify({"status": "Error", "message": "SMTP authentication failed", "reason": "Invalid SMTP_USERNAME or SMTP_PASSWORD. If using Gmail, ensure you are using an App Password (not your regular password) with 2-Step Verification enabled"}), 500
    except smtplib.SMTPRecipientsRefused:
        return jsonify({"status": "Error", "message": "Recipient email rejected", "reason": "The recipient email address was rejected by the mail server. Check if the email address is valid"}), 500
    except smtplib.SMTPSenderRefused:
        return jsonify({"status": "Error", "message": "Sender email rejected", "reason": "The sender email (SMTP_FROM_EMAIL) was rejected. Ensure it matches your SMTP account"}), 500
    except smtplib.SMTPConnectError:
        return jsonify({"status": "Error", "message": "Failed to connect to SMTP server", "reason": f"Cannot connect to {SMTP_HOST}:{SMTP_PORT}. Check SMTP_HOST and SMTP_PORT environment variables"}), 500
    except smtplib.SMTPServerDisconnected:
        return jsonify({"status": "Error", "message": "SMTP server disconnected", "reason": "Connection to SMTP server was lost. This may be due to network issues or server timeout"}), 500
    except smtplib.SMTPException as e:
        return jsonify({"status": "Error", "message": f"Failed to send email: {str(e)}", "reason": "General SMTP error. Check SMTP configuration and ensure all environment variables are correctly set"}), 500
    except Exception as e:
        return jsonify({"status": "Error", "message": f"Unexpected error: {str(e)}", "reason": "An unexpected error occurred. Check server logs for more details"}), 500


@app.post("/api/updatestatus")
def update_email_status():
    """Update email_verified status for a user."""
    email = request.headers.get("email", "").strip()

    if not email:
        return jsonify({"status": "Error", "message": "Email is required in header"}), 400

    try:
        # Check if user exists
        rows = execute_query(
            "SELECT id, email_verified FROM users WHERE email = %s",
            (email,),
            fetch=True
        )

        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        current_status = rows[0][1]

        # If already verified, return success
        if current_status == 1:
            return jsonify({"status": "OK", "message": "Email already verified"}), 200

        # Update email_verified to true (1)
        execute_query(
            "UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE email = %s",
            (email,)
        )

        return jsonify({"status": "OK", "message": "Email verified successfully"}), 200
    except (OperationalError, DatabaseError) as e:
        return jsonify({"status": "Error", "message": "Database error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
