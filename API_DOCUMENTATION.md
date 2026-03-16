# API Documentation

Base URL (local): `http://localhost:5000`  
Base URL (production): `https://system-project-api.onrender.com`

WebSocket Endpoint: `https://system-project-api.onrender.com/socket.io/`

---

## REST API Endpoints

### 1. Health Check

**GET** `/`

Returns a simple status message to confirm the API is running.

**Response — 200 OK**
```json
{
  "message": "Flask API running on Render",
  "websocket_endpoint": "/socket.io/",
  "total_tick_sequences": 3601
}
```

---

### 2. Check Database Connection

**GET** `/api/checkconnection`

Tests PostgreSQL database connectivity and diagnoses connection issues.

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"status": "OK", "message": "Successfully connected"}` | Database connection successful |
| 500 | `{"status": "Error", "problem": "<diagnosis>"}` | Connection failed with specific diagnosis |

**Possible Diagnoses:**
- `DATABASE_URL environment variable is not set`
- `Access denied — wrong username or password`
- `Database does not exist — check DATABASE_URL`
- `Cannot connect to host — wrong host/port or server is down`
- `Unknown host — check hostname in DATABASE_URL`

**Example Request**
```bash
curl https://system-project-api.onrender.com/api/checkconnection
```

---

### 3. Login

**POST** `/api/login`

Authenticates a user with their email or phone number and password.

**Request Body** (`application/json` or `form-data`)

| Field      | Type   | Required | Description                          |
|------------|--------|----------|--------------------------------------|
| `user_id`  | string | ✅       | User's email or phone number         |
| `password` | string | ✅       | User's password                      |

**Responses**

| Status | Body                                                                 | Meaning                        |
|--------|----------------------------------------------------------------------|--------------------------------|
| 200    | `{"status": "OK", "message": "Login successful"}`                   | Login successful (ACTIVE)      |
| 400    | `{"status": "Error", "message": "user_id and password are required"}` | Missing fields               |
| 401    | `{"status": "Error", "message": "Invalid credentials"}`             | Wrong email/phone or password  |
| 403    | `{"status": "Error", "message": "Account is blocked"}`              | Account status is BLOCKED      |
| 403    | `{"status": "Error", "message": "Account is inactive"}`             | Account status is not ACTIVE   |
| 500    | `{"status": "Error", "message": "Database connection failed"}`      | Database error                 |

**Example Request**
```bash
curl -X POST https://system-project-api.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john@example.com", "password": "secret123"}'
```

---

### 4. Signup

**POST** `/api/signup`

Registers a new user account.

**Request Body** (`application/json` or `form-data`)

| Field          | Type   | Required | Description                        |
|----------------|--------|----------|------------------------------------|
| `first_name`   | string | ✅       | User's first name                  |
| `last_name`    | string | ✅       | User's last name                   |
| `email`        | string | ✅       | Valid email address                |
| `username`     | string | ✅       | Unique username                    |
| `phone_number` | string | ✅       | Phone number (min. 10 digits)      |
| `password`     | string | ✅       | Password (min. 6 characters)       |

**Responses**

| Status | Body                                                                          | Meaning                            |
|--------|-------------------------------------------------------------------------------|------------------------------------|
| 201    | `{"status": "OK", "message": "User registered successfully"}`                | Account created successfully       |
| 400    | `{"status": "Error", "message": "Missing required fields: <fields>"}`        | One or more fields missing         |
| 400    | `{"status": "Error", "message": "Invalid email format"}`                     | Email format is invalid            |
| 400    | `{"status": "Error", "message": "Phone number must be at least 10 digits"}`  | Phone number too short             |
| 400    | `{"status": "Error", "message": "Password must be at least 6 characters"}`   | Password too short                 |
| 409    | `{"status": "Error", "message": "Email already registered"}`                 | Email already exists               |
| 409    | `{"status": "Error", "message": "Phone number already registered"}`          | Phone number already exists        |
| 409    | `{"status": "Error", "message": "Username already taken"}`                   | Username already exists            |
| 500    | `{"status": "Error", "message": "Database connection failed"}`               | Database error                     |

**Example Request**
```bash
curl -X POST https://system-project-api.onrender.com/api/signup \
  -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Doe", "email": "john@example.com", "username": "johndoe", "phone_number": "1234567890", "password": "secret123"}'
```

---

### 5. Send OTP

**POST** `/api/sendotp`

Sends an OTP verification code to the specified email address.

**Request Body** (`application/json` or `form-data`)

| Field   | Type   | Required | Description                |
|---------|--------|----------|----------------------------|
| `email` | string | ✅       | Recipient's email address  |
| `otp`   | string | ✅       | OTP code to send           |

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"status": "OK", "message": "OTP sent successfully"}` | Email sent |
| 400 | `{"status": "Error", "message": "Email is required"}` | Missing email |
| 400 | `{"status": "Error", "message": "OTP is required"}` | Missing OTP |
| 500 | `{"status": "Error", "message": "SMTP authentication failed", "reason": "..."}` | SMTP auth error |

**Example Request**
```bash
curl -X POST https://system-project-api.onrender.com/api/sendotp \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "otp": "123456"}'
```

---

### 6. Update Email Status

**POST** `/api/updatestatus`

Marks a user's email as verified.

**Request Body** (`application/json` or `form-data`)

| Field   | Type   | Required | Description           |
|---------|--------|----------|-----------------------|
| `email` | string | ✅       | User's email address  |

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"status": "OK", "message": "Email verified successfully"}` | Email marked as verified |
| 200 | `{"status": "OK", "message": "Email already verified"}` | Already verified |
| 400 | `{"status": "Error", "message": "Email is required"}` | Missing email |
| 404 | `{"status": "Error", "message": "User not found"}` | No user with this email |
| 500 | `{"status": "Error", "message": "Database error"}` | Database error |

**Example Request**
```bash
curl -X POST https://system-project-api.onrender.com/api/updatestatus \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 7. Forgot Password

**POST** `/api/forgotpassword`

Initiates a password reset by verifying the provided email or phone number exists in the system and sending an OTP to the registered email address.

**Request Body** (`application/json` or `form-data`)

**Headers**

| Header         | Value              | Required |
|----------------|--------------------|----------|
| `Content-Type` | `application/json` | ✅       |

| Field          | Type   | Required | Description                                      |
|----------------|--------|----------|--------------------------------------------------|
| `email`        | string | ❌       | User's registered email address                  |
| `phone_number` | string | ❌       | User's registered phone number                   |

> **Note:** At least one of `email` or `phone_number` must be provided. If both are provided, `email` takes priority.

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"status": "OK", "message": "OTP sent successfully to the registered email", "otp": "482917"}` | OTP generated and sent to the user's email |
| 400 | `{"status": "Error", "message": "Email or phone number is required"}` | Neither email nor phone number provided |
| 404 | `{"status": "Error", "message": "No account found with the provided email or phone number"}` | No matching user found |
| 500 | `{"status": "Error", "message": "SMTP authentication failed"}` | SMTP auth error |
| 500 | `{"status": "Error", "message": "Failed to send email: <details>"}` | Email sending failed |
| 500 | `{"status": "Error", "message": "Database connection failed"}` | Database error |

**Example Request (with email)**
```bash
curl -X POST https://system-project-api.onrender.com/api/forgotpassword \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'
```

**Example Request (with phone number)**
```bash
curl -X POST https://system-project-api.onrender.com/api/forgotpassword \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "1234567890"}'
```

**Success Response**
```json
{
  "status": "OK",
  "message": "OTP sent successfully to the registered email",
  "otp": "482917"
}
```

---

### 8. Reset Password

**POST** `/api/resetpassword`

Updates the user's password after OTP verification. Finds the user by email or phone number and updates the password.

**Headers**

| Header         | Value              | Required |
|----------------|--------------------|----------|
| `Content-Type` | `application/json` | ✅       |

**Request Body** (`application/json` or `form-data`)

| Field          | Type   | Required | Description                                      |
|----------------|--------|----------|--------------------------------------------------|
| `email`        | string | ❌       | User's registered email address                  |
| `phone_number` | string | ❌       | User's registered phone number                   |
| `password`     | string | ✅       | New password (min. 6 characters)                 |

> **Note:** At least one of `email` or `phone_number` must be provided. If both are provided, `email` takes priority.

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"status": "OK", "message": "Password updated successfully"}` | Password updated |
| 400 | `{"status": "Error", "message": "Email or phone number is required"}` | Neither email nor phone number provided |
| 400 | `{"status": "Error", "message": "Password is required"}` | Password not provided |
| 400 | `{"status": "Error", "message": "Password must be at least 6 characters"}` | Password too short |
| 404 | `{"status": "Error", "message": "No account found with the provided email or phone number"}` | No matching user found |
| 500 | `{"status": "Error", "message": "Database connection failed"}` | Database error |

**Example Request (with email)**
```bash
curl -X POST https://system-project-api.onrender.com/api/resetpassword \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "newpassword123"}'
```

**Example Request (with phone number)**
```bash
curl -X POST https://system-project-api.onrender.com/api/resetpassword \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "1234567890", "password": "newpassword123"}'
```

**Success Response**
```json
{
  "status": "OK",
  "message": "Password updated successfully"
}
```

---

### 9. Ticks Info

**GET** `/api/ticks/info`

Returns information about available tick data for WebSocket streaming.

**Response — 200 OK**
```json
{
  "status": "OK",
  "total_sequences": 3601,
  "connected_clients": 3,
  "broadcast_interval": "3 seconds"
}
```

---

---

## WebSocket Events

WebSocket Endpoint: `https://system-project-api.onrender.com/socket.io/`

### Connection Flow

```
Android App                              Server
    |                                       |
    |-------- Connect WebSocket ----------->|
    |<------ connection_status -------------|
    |                                       |
    |-------- start_ticks ----------------->|
    |<------ tick_data (STARTED) -----------|
    |<------ tick_data (sequence 1) --------|  (3 sec)
    |<------ tick_data (sequence 2) --------|  (3 sec)
    |<------ tick_data (sequence 3) --------|  (3 sec)
    |           ...                         |
    |<------ tick_data (COMPLETED) ---------|
    |                                       |
    |-------- Reconnect ------------------->|  (to restart from 1)
```

---

### Client → Server Events

#### `start_ticks`

Start receiving tick data. Broadcasts begin from sequence 1.

**Payload:** None

**Server Response:**
```json
{
  "status": "STARTED",
  "message": "Tick broadcasting started",
  "total_sequences": 3601
}
```

---

#### `stop_ticks`

Stop receiving tick data.

**Payload:** None

**Server Response:**
```json
{
  "status": "STOPPED",
  "message": "Tick broadcasting stopped"
}
```

---

### Server → Client Events

#### `connection_status`

Sent immediately upon WebSocket connection.

```json
{
  "status": "connected",
  "client_id": "abc123xyz",
  "total_sequences": 3601,
  "message": "Send \"start_ticks\" event to begin receiving data"
}
```

---

#### `tick_data`

Sent every 3 seconds after `start_ticks` is triggered.

**During Broadcasting:**
```json
{
  "status": "OK",
  "data": {
    "sequence": 1,
    "time": "2025-10-01 09:15:00",
    "ticks": [
      {
        "symbol": "NIFTY50",
        "price": 22430.58,
        "previous_price": 22430.0
      },
      {
        "symbol": "SENSEX",
        "price": 73420.1,
        "previous_price": 73420.0
      },
      {
        "symbol": "BANKNIFTY",
        "price": 48508.64,
        "previous_price": 48510.0
      }
    ]
  },
  "is_last": false
}
```

**When All Sequences Sent:**
```json
{
  "status": "COMPLETED",
  "message": "All sequences sent. Reconnect to restart.",
  "total_sequences": 3601
}
```

---

## Android Integration Example

### Dependencies (build.gradle)
```gradle
implementation 'io.socket:socket.io-client:2.1.0'
```

### Kotlin Example
```kotlin
import io.socket.client.IO
import io.socket.client.Socket
import org.json.JSONObject

class TickService {
    private lateinit var socket: Socket
    
    fun connect() {
        val options = IO.Options().apply {
            transports = arrayOf("websocket")
            secure = true
        }
        socket = IO.socket("https://system-project-api.onrender.com", options)
        
        socket.on(Socket.EVENT_CONNECT) {
            println("Connected to WebSocket")
        }
        
        socket.on("connection_status") { args ->
            val data = args[0] as JSONObject
            println("Status: ${data.getString("status")}")
        }
        
        socket.on("tick_data") { args ->
            val data = args[0] as JSONObject
            when (data.getString("status")) {
                "OK" -> {
                    val tickData = data.getJSONObject("data")
                    val sequence = tickData.getInt("sequence")
                    val ticks = tickData.getJSONArray("ticks")
                    // Process tick data
                }
                "COMPLETED" -> {
                    // All data received
                }
            }
        }
        
        socket.connect()
    }
    
    fun startTicks() {
        socket.emit("start_ticks")
    }
    
    fun stopTicks() {
        socket.emit("stop_ticks")
    }
    
    fun disconnect() {
        socket.disconnect()
    }
}
```

---

## Testing WebSocket

### Browser Console Test
```javascript
var s = document.createElement('script');
s.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
s.onload = () => {
    const socket = io('https://system-project-api.onrender.com');
    socket.on('connect', () => {
        console.log('Connected!');
        socket.emit('start_ticks');
    });
    socket.on('tick_data', console.log);
};
document.head.appendChild(s);
```

---

## Error Format

All error responses follow this structure:
```json
{
  "status": "Error",
  "message": "<description of the error>"
}
```

Some errors include additional context:
```json
{
  "status": "Error",
  "message": "<error description>",
  "reason": "<detailed explanation>"
}
```
