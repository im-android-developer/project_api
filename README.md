# project_api

## Environment Variables

Set these environment variables in your Render dashboard for SMTP email functionality:

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP login username/email | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP password or app password | `your-app-password` |
| `SMTP_FROM_EMAIL` | Sender email address (optional, defaults to SMTP_USERNAME) | `noreply@yourdomain.com` |

### Gmail Setup
If using Gmail, enable "App Passwords" in your Google account:
1. Go to Google Account → Security → 2-Step Verification
2. Enable 2-Step Verification if not already enabled
3. Go to App Passwords → Generate a new app password
4. Use this generated password as `SMTP_PASSWORD`

## API Endpoints

### POST `/api/sendotp`
Send OTP to an email address.

**Headers:**
- `email`: Recipient email address
- `otp`: OTP code to send

**Response:**
```json
{"status": "OK", "message": "OTP sent successfully"}
```

### POST `/api/updatestatus`
Update email verification status for a user.

**Headers:**
- `email`: User's email address

**Response:**
```json
{"status": "OK", "message": "Email verified successfully"}
```