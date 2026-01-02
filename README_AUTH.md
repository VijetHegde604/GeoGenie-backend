# Authentication Guide

GeoGenie API now supports authentication using either HTTP Basic Auth or JWT Bearer tokens.

## Default Credentials

The following users are pre-configured:

- **Username:** `admin` / **Password:** `admin123`
- **Username:** `user` / **Password:** `user123`

⚠️ **Change these passwords in production!**

## Authentication Methods

### 1. HTTP Basic Authentication

Include credentials in the Authorization header:

```bash
curl -u admin:admin123 http://localhost:8000/recognize \
  -F "image=@photo.jpg"
```

Or in code:
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    'http://localhost:8000/recognize',
    files={'image': open('photo.jpg', 'rb')},
    auth=HTTPBasicAuth('admin', 'admin123')
)
```

### 2. JWT Bearer Token

**Step 1: Login to get token**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin"
}
```

**Step 2: Use token in requests**
```bash
curl -X POST http://localhost:8000/recognize \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "image=@photo.jpg"
```

Or in code:
```python
import requests

token = "YOUR_TOKEN_HERE"
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    'http://localhost:8000/recognize',
    files={'image': open('photo.jpg', 'rb')},
    headers=headers
)
```

## Protected Endpoints

All API endpoints (except `/` and `/auth/login`) require authentication:

- `POST /recognize` - Requires auth
- `POST /feedback` - Requires auth
- `GET /placeinfo/{name}` - Requires auth
- `GET /auth/me` - Requires auth (returns current user info)

## Public Endpoints

- `GET /` - Health check (no auth required)
- `POST /auth/login` - Login endpoint (no auth required)

## Frontend Integration

Update your frontend API client to include authentication:

```typescript
// services/api.ts
import axios from 'axios';

// Store token after login
let authToken: string | null = null;

export function setAuthToken(token: string) {
  authToken = token;
}

// Add token to all requests
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': authToken ? `Bearer ${authToken}` : undefined,
  },
});

// Or use Basic Auth
const api = axios.create({
  baseURL: API_BASE_URL,
  auth: {
    username: 'admin',
    password: 'admin123',
  },
});
```

## Security Notes

1. **Change default passwords** - Update user passwords in `auth.py`
2. **Use HTTPS in production** - Never send credentials over HTTP
3. **Set JWT_SECRET_KEY** - Use environment variable for secret key
4. **Token expiration** - Tokens expire after 24 hours (configurable)
5. **Rate limiting** - Consider adding rate limiting for production

## Adding New Users

Edit `backend/auth.py` and add to `USERS_DB`:

```python
USERS_DB = {
    "newuser": {
        "hashed_password": pwd_context.hash("secure_password"),
        "disabled": False,
    }
}
```

