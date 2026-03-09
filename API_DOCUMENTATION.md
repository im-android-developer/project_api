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

Authenticates a user with their login ID and password.

**Request Body** (`application/json` or `form-data`)

| Field       | Type   | Required | Description         |
|-------------|--------|----------|---------------------|
| `login_id`  | string | ✅       | User's login ID     |
| `login_pwd` | string | ✅       | User's password     |

**Responses**

| Status | Body                                                                 | Meaning                        |
|--------|----------------------------------------------------------------------|--------------------------------|
| 200    | `{"status": "OK"}`                                                   | Login successful               |
| 400    | `{"status": "Error", "message": "login_id and login_pwd are required"}` | Missing fields              |
| 401    | `{"status": "Error", "message": "Invalid login_id or login_pwd"}`   | Wrong credentials              |

**Example Request**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"login_id": "demo", "login_pwd": "demo123"}'
```

**Example Response**
```json
{"status": "OK"}
```

---

## 3. Signup

**POST** `/api/signup`

Registers a new user account.

**Request Body** (`application/json` or `form-data`)

| Field       | Type   | Required | Description                     |
|-------------|--------|----------|---------------------------------|
| `full_name` | string | ✅       | User's full name                |
| `username`  | string | ✅       | Unique username                 |
| `email`     | string | ✅       | Valid email address             |
| `password`  | string | ✅       | Password (min. 6 characters)    |

**Responses**

| Status | Body                                                                          | Meaning                        |
|--------|-------------------------------------------------------------------------------|--------------------------------|
| 201    | `{"status": "OK"}`                                                            | Account created successfully   |
| 400    | `{"status": "Error", "message": "Missing required fields: <fields>"}`        | One or more fields missing     |
| 400    | `{"status": "Error", "message": "Invalid email format"}`                     | Email format is invalid        |
| 400    | `{"status": "Error", "message": "Password must be at least 6 characters"}`   | Password too short             |

**Example Request**
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Tarun Singh", "username": "tarun", "email": "tarun@example.com", "password": "secret123"}'
```

**Example Response**
```json
{"status": "OK"}
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
