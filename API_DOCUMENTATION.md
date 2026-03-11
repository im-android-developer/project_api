# API Documentation

Base URL (local): `http://localhost:5000`  
Base URL (production): `https://<your-render-app>.onrender.com`

---

## 1. Health Check

**GET** `/`

Returns a simple status message to confirm the API is running.

**Response — 200 OK**
```json
{
  "message": "Flask API running on Render"
}
```

---

## 2. Login

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

**Example Request**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john@example.com", "password": "secret123"}'
```

**Example Response**
```json
{"status": "OK", "message": "Login successful"}
```

---

## 3. Signup

**POST** `/api/signup`

Registers a new user account.

**Request Body** (`application/json` or `form-data`)

| Field          | Type   | Required | Description                        |
|----------------|--------|----------|------------------------------------|
| `first_name`   | string | ✅       | User's first name                  |
| `last_name`    | string | ✅       | User's last name                   |
| `email`        | string | ✅       | Valid email address                |
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

**Example Request**
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Doe", "email": "john@example.com", "phone_number": "1234567890", "password": "secret123"}'
```

**Example Response**
```json
{"status": "OK", "message": "User registered successfully"}
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
