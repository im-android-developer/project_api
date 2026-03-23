import os
import json
import hashlib
import random
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from db import get_connection, execute_query
from psycopg2 import OperationalError, DatabaseError

# SMTP Configuration (set these in Render environment variables)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "enfec.tarunbansal@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "vffbushrlfxoczmc")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "enfec.tarunbansal@gmail.com")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f9e4bbf6ee3e71f192f45073e9bf025bbb9d3438e216482e487f3233ca7668de'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# ==================== UTILITY FUNCTIONS ====================

def hash_password(password):
    """SHA-256 hash — replace with bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


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


# ==================== TICK DATA MANAGEMENT ====================

def load_ticks_data():
    """Load tick data from index_ticks.json"""
    try:
        with open('index_ticks.json', 'r') as f:
            data = json.load(f)
            return data.get('events', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading ticks data: {e}")
        return []


def load_companies_data():
    """Load companies data from companies.json"""
    try:
        with open('companies.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading companies data: {e}")
        return {}


def load_market_data():
    """Load market data from market_data.json"""
    try:
        with open('market_data.json', 'r') as f:
            data = json.load(f)
            return data.get('events', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading market data: {e}")
        return []


# Global state for WebSocket
ticks_data = load_ticks_data()
market_data = load_market_data()
connected_clients = set()
broadcast_threads = {}
market_broadcast_threads = {}


class TickBroadcaster:
    """Manages tick broadcasting for a client"""
    
    def __init__(self, client_id):
        self.client_id = client_id
        self.current_index = 0
        self.running = False
    
    def start(self):
        """Start broadcasting ticks"""
        if self.running:
            return
        
        self.running = True
        self.current_index = 0
        thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop broadcasting"""
        self.running = False
    
    def _broadcast_loop(self):
        """Main broadcast loop - sends tick every 3 seconds"""
        while self.running and self.current_index < len(ticks_data):
            if self.client_id not in connected_clients:
                self.running = False
                break
            
            event = ticks_data[self.current_index]
            
            if event and 'sequence' in event:
                socketio.emit('tick_data', {
                    'status': 'OK',
                    'data': event,
                    'is_last': self.current_index == len(ticks_data) - 1
                }, room=self.client_id)
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Sent sequence {event.get('sequence')} to client {self.client_id}")
            
            self.current_index += 1
            
            if self.running and self.current_index < len(ticks_data):
                socketio.sleep(3)
        
        if self.running and self.current_index >= len(ticks_data):
            socketio.emit('tick_data', {
                'status': 'COMPLETED',
                'message': 'All sequences sent. Reconnect to restart.',
                'total_sequences': len(ticks_data)
            }, room=self.client_id)
            self.running = False
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Broadcast completed for client {self.client_id}")

class MarketDataBroadcaster:
    """Manages market data broadcasting for a client"""

    def __init__(self, client_id):
        self.client_id = client_id
        self.current_index = 0
        self.running = False

    def start(self):
        """Start broadcasting market data"""
        if self.running:
            return

        self.running = True
        self.current_index = 0
        thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        thread.start()

    def stop(self):
        """Stop broadcasting"""
        self.running = False

    def _broadcast_loop(self):
        """Main broadcast loop - sends market data every 3 seconds"""
        while self.running and self.current_index < len(market_data):
            if self.client_id not in connected_clients:
                self.running = False
                break

            event = market_data[self.current_index]

            if event and 'sequence' in event:
                socketio.emit('market_data', {
                    'status': 'OK',
                    'data': event,
                    'is_last': self.current_index == len(market_data) - 1
                }, room=self.client_id)

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Sent market sequence {event.get('sequence')} to client {self.client_id}")

            self.current_index += 1

            if self.running and self.current_index < len(market_data):
                socketio.sleep(3)

        if self.running and self.current_index >= len(market_data):
            socketio.emit('market_data', {
                'status': 'COMPLETED',
                'message': 'All market data sequences sent. Reconnect to restart.',
                'total_sequences': len(market_data)
            }, room=self.client_id)
            self.running = False
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Market data broadcast completed for client {self.client_id}")


@app.route("/")
def home():
    return jsonify({
        "message": "Flask API running on Render",
        "websocket_endpoint": "/socket.io/",
        "total_tick_sequences": len(ticks_data)
    })

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
            account_status = rows[0]['account_status']
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


@app.post("/api/sendotp")
def send_otp():
    """Send OTP to the specified email address."""
    data = request.get_json(silent=True) or request.form or {}
    email = (data.get("email") or "").strip()
    otp = (data.get("otp") or "").strip()

    if not email:
        return jsonify({"status": "Error", "message": "Email is required"}), 400
    if not otp:
        return jsonify({"status": "Error", "message": "OTP is required"}), 400

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
    data = request.get_json(silent=True) or request.form or {}
    email = (data.get("email") or "").strip()

    if not email:
        return jsonify({"status": "Error", "message": "Email is required"}), 400

    try:
        # Check if user exists
        rows = execute_query(
            "SELECT id, email_verified FROM users WHERE email = %s",
            (email,),
            fetch=True
        )

        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        current_status = rows[0]['email_verified']

        # If already verified, return success
        if current_status == True:
            return jsonify({"status": "OK", "message": "Email already verified"}), 200

        # Update email_verified to true
        execute_query(
            "UPDATE users SET email_verified = TRUE, updated_at = CURRENT_TIMESTAMP WHERE email = %s",
            (email,)
        )

        return jsonify({"status": "OK", "message": "Email verified successfully"}), 200
    except (OperationalError, DatabaseError) as e:
        return jsonify({"status": "Error", "message": "Database error"}), 500


@app.post("/api/forgotpassword")
def forgot_password():
    """Send OTP for password reset after verifying email or phone exists."""
    data = request.get_json(silent=True) or request.form or {}
    email = (data.get("email") or "").strip()
    phone_number = (data.get("phone_number") or "").strip()

    if not email and not phone_number:
        return jsonify({"status": "Error", "message": "Email or phone number is required"}), 400

    try:
        # Check if the user exists by email or phone_number
        if email:
            rows = execute_query(
                "SELECT id, email FROM users WHERE email = %s",
                (email,),
                fetch=True
            )
        else:
            rows = execute_query(
                "SELECT id, email FROM users WHERE phone_number = %s",
                (phone_number,),
                fetch=True
            )

        if not rows:
            return jsonify({"status": "Error", "message": "No account found with the provided email or phone number"}), 404

        user_email = rows[0]['email']

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Send OTP to the user's email
        subject = "Password Reset OTP"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>Dear User,</p>
            <p>We received a request to reset your password. Use the OTP below to proceed:</p>
            <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; text-align: center;">
                <h1 style="color: #333; letter-spacing: 5px;">{otp}</h1>
            </div>
            <p>This OTP is valid for a limited time. Please do not share it with anyone.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Support Team</p>
        </body>
        </html>
        """
        send_email(user_email, subject, body)

        return jsonify({"status": "OK", "message": "OTP sent successfully to the registered email", "otp": otp}), 200

    except smtplib.SMTPAuthenticationError:
        return jsonify({"status": "Error", "message": "SMTP authentication failed"}), 500
    except smtplib.SMTPException as e:
        return jsonify({"status": "Error", "message": f"Failed to send email: {str(e)}"}), 500
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


@app.post("/api/resetpassword")
def reset_password():
    """Update user password after forgot password verification."""
    data = request.get_json(silent=True) or request.form or {}
    email = (data.get("email") or "").strip()
    phone_number = (data.get("phone_number") or "").strip()
    password = (data.get("password") or "").strip()

    if not email and not phone_number:
        return jsonify({"status": "Error", "message": "Email or phone number is required"}), 400

    if not password:
        return jsonify({"status": "Error", "message": "Password is required"}), 400

    if len(password) < 6:
        return jsonify({"status": "Error", "message": "Password must be at least 6 characters"}), 400

    try:
        # Check if user exists
        if email:
            rows = execute_query(
                "SELECT id FROM users WHERE email = %s",
                (email,),
                fetch=True
            )
        else:
            rows = execute_query(
                "SELECT id FROM users WHERE phone_number = %s",
                (phone_number,),
                fetch=True
            )

        if not rows:
            return jsonify({"status": "Error", "message": "No account found with the provided email or phone number"}), 404

        # Update password
        hashed = hash_password(password)
        if email:
            execute_query(
                "UPDATE users SET password = %s, updated_at = CURRENT_TIMESTAMP WHERE email = %s",
                (hashed, email)
            )
        else:
            execute_query(
                "UPDATE users SET password = %s, updated_at = CURRENT_TIMESTAMP WHERE phone_number = %s",
                (hashed, phone_number)
            )

        return jsonify({"status": "OK", "message": "Password updated successfully"}), 200

    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


# ==================== KYC & WALLET ENDPOINTS ====================

@app.route("/api/kyc-status")
def kyc_status():
    """Check KYC status of a user."""
    user_id = request.args.get("user_id", "").strip()

    if not user_id:
        return jsonify({"status": "Error", "message": "user_id is required"}), 400

    try:
        rows = execute_query(
            "SELECT id, kyc_status FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        return jsonify({
            "status": "OK",
            "user_id": rows[0]["id"],
            "kyc_status": rows[0]["kyc_status"]
        }), 200
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


@app.route("/api/wallet-balance")
def wallet_balance():
    """Fetch wallet balance of a user."""
    user_id = request.args.get("user_id", "").strip()

    if not user_id:
        return jsonify({"status": "Error", "message": "user_id is required"}), 400

    try:
        rows = execute_query(
            "SELECT id, wallet_balance FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        return jsonify({
            "status": "OK",
            "user_id": rows[0]["id"],
            "wallet_balance": float(rows[0]["wallet_balance"])
        }), 200
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


@app.post("/api/wallet-update")
def wallet_update():
    """Update wallet balance when user adds or withdraws amount."""
    data = request.get_json(silent=True) or request.form or {}
    user_id = (data.get("user_id") or "").strip()
    amount = data.get("amount")
    transaction_type = (data.get("transaction_type") or "").strip().lower()

    if not user_id:
        return jsonify({"status": "Error", "message": "user_id is required"}), 400
    if amount is None or amount == "":
        return jsonify({"status": "Error", "message": "amount is required"}), 400
    if transaction_type not in ("credit", "debit"):
        return jsonify({"status": "Error", "message": "transaction_type must be 'credit' or 'debit'"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"status": "Error", "message": "amount must be a valid number"}), 400

    if amount <= 0:
        return jsonify({"status": "Error", "message": "amount must be greater than 0"}), 400

    try:
        rows = execute_query(
            "SELECT id, wallet_balance FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        current_balance = float(rows[0]["wallet_balance"])

        if transaction_type == "debit" and amount > current_balance:
            return jsonify({"status": "Error", "message": "Insufficient wallet balance"}), 400

        if transaction_type == "credit":
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount

        execute_query(
            "UPDATE users SET wallet_balance = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_balance, user_id)
        )

        return jsonify({
            "status": "OK",
            "message": f"Wallet {'credited' if transaction_type == 'credit' else 'debited'} successfully",
            "previous_balance": current_balance,
            "amount": amount,
            "transaction_type": transaction_type,
            "new_balance": new_balance
        }), 200
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


@app.post("/api/transactions")
def record_transaction():
    """Record a user transaction."""
    data = request.get_json(silent=True) or request.form or {}
    user_id = (data.get("user_id") or "").strip()
    amount = data.get("amount")
    transaction_type = (data.get("transaction_type") or "").strip().lower()
    status = (data.get("status") or "").strip()

    if not user_id:
        return jsonify({"status": "Error", "message": "user_id is required"}), 400
    if amount is None or amount == "":
        return jsonify({"status": "Error", "message": "amount is required"}), 400
    if transaction_type not in ("credit", "debit"):
        return jsonify({"status": "Error", "message": "transaction_type must be 'credit' or 'debit'"}), 400
    if status not in ("Successful", "Pending", "Failed"):
        return jsonify({"status": "Error", "message": "status must be 'Successful', 'Pending', or 'Failed'"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"status": "Error", "message": "amount must be a valid number"}), 400

    if amount <= 0:
        return jsonify({"status": "Error", "message": "amount must be greater than 0"}), 400

    try:
        # Verify user exists
        rows = execute_query(
            "SELECT id FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        if not rows:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        tr_id = execute_query(
            "INSERT INTO transactions (user_id, amount, transaction_type, status) VALUES (%s, %s, %s, %s) RETURNING tr_id",
            (user_id, amount, transaction_type, status)
        )

        return jsonify({
            "status": "OK",
            "message": "Transaction recorded successfully",
            "tr_id": tr_id,
            "user_id": int(user_id),
            "amount": amount,
            "transaction_type": transaction_type,
            "transaction_status": status
        }), 201
    except (OperationalError, DatabaseError):
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500


# ==================== COMPANIES ENDPOINT ====================

@app.route("/api/companies")
def get_companies():
    """Return companies data from companies.json"""
    data = load_companies_data()
    if not data:
        return jsonify({"status": "Error", "message": "No companies data available"}), 500
    return jsonify({"status": "OK", "data": data}), 200


# ==================== TICK DATA ENDPOINTS ====================

@app.route("/api/ticks/info")
def ticks_info():
    """Get info about available tick data"""
    return jsonify({
        "status": "OK",
        "total_sequences": len(ticks_data),
        "connected_clients": len(connected_clients),
        "broadcast_interval": "3 seconds"
    })


# ==================== WEBSOCKET EVENT HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    client_id = request.sid
    connected_clients.add(client_id)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Client connected: {client_id}")
    
    emit('connection_status', {
        'status': 'connected',
        'client_id': client_id,
        'total_sequences': len(ticks_data),
        'message': 'Send "start_ticks" event to begin receiving data'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    client_id = request.sid
    
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
        del broadcast_threads[client_id]
    
    if client_id in market_broadcast_threads:
        market_broadcast_threads[client_id].stop()
        del market_broadcast_threads[client_id]
    
    connected_clients.discard(client_id)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Client disconnected: {client_id}")


@socketio.on('start_ticks')
def handle_start_ticks():
    """Start broadcasting ticks to the client"""
    global ticks_data
    client_id = request.sid
    
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
    
    ticks_data = load_ticks_data()
    
    if not ticks_data:
        emit('tick_data', {
            'status': 'Error',
            'message': 'No tick data available'
        })
        return
    
    broadcaster = TickBroadcaster(client_id)
    broadcast_threads[client_id] = broadcaster
    broadcaster.start()
    
    emit('tick_data', {
        'status': 'STARTED',
        'message': 'Tick broadcasting started',
        'total_sequences': len(ticks_data)
    })


@socketio.on('stop_ticks')
def handle_stop_ticks():
    """Stop broadcasting ticks to the client"""
    client_id = request.sid
    
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
        del broadcast_threads[client_id]
        
        emit('tick_data', {
            'status': 'STOPPED',
            'message': 'Tick broadcasting stopped'
        })
    else:
        emit('tick_data', {
            'status': 'Info',
            'message': 'No active broadcast to stop'
        })


# ==================== MARKET DATA WEBSOCKET HANDLERS ====================

@socketio.on('start_market_data')
def handle_start_market_data():
    """Start broadcasting market data to the client"""
    global market_data
    client_id = request.sid

    if client_id in market_broadcast_threads:
        market_broadcast_threads[client_id].stop()

    market_data = load_market_data()

    if not market_data:
        emit('market_data', {
            'status': 'Error',
            'message': 'No market data available'
        })
        return

    broadcaster = MarketDataBroadcaster(client_id)
    market_broadcast_threads[client_id] = broadcaster
    broadcaster.start()

    emit('market_data', {
        'status': 'STARTED',
        'message': 'Market data broadcasting started',
        'total_sequences': len(market_data)
    })


@socketio.on('stop_market_data')
def handle_stop_market_data():
    """Stop broadcasting market data to the client"""
    client_id = request.sid

    if client_id in market_broadcast_threads:
        market_broadcast_threads[client_id].stop()
        del market_broadcast_threads[client_id]

        emit('market_data', {
            'status': 'STOPPED',
            'message': 'Market data broadcasting stopped'
        })
    else:
        emit('market_data', {
            'status': 'Info',
            'message': 'No active market data broadcast to stop'
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"Starting server on port {port}")
    print(f"Loaded {len(ticks_data)} tick sequences")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
