# GeoGenie Authentication Notes (Current State)

## Important status

Authentication helpers exist in `auth.py`, including:

- HTTP Basic verification
- JWT issuance and validation
- optional user lookup helpers

However, **the current `main.py` routes are not protected by auth dependencies**. That means endpoints are accessible without credentials unless you explicitly wire dependencies into route definitions.

---

## What is implemented in code

- Password hashing via `passlib` + bcrypt
- JWT token creation (`HS256`)
- Token decode/validation helpers
- DB-backed user authentication (via `crud.py` + `SessionLocal`)

Environment variable used when JWT is enabled:

- `JWT_SECRET_KEY` (falls back to insecure default if unset)

---

## Secure-by-default recommendation

If you plan to enforce authentication now, do all of the following:

1. Add `Depends(get_current_user)` to protected routes in `main.py`.
2. Keep `POST /auth/login` and `GET /` public.
3. Set a strong `JWT_SECRET_KEY`.
4. Use HTTPS in production.
5. Rotate credentials and avoid default/testing passwords.

---

## Example auth flow (after wiring endpoints)

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me"}'
```

### Call protected endpoint
```bash
curl -X POST http://localhost:8000/recognize \
  -H "Authorization: Bearer <TOKEN>" \
  -F "image=@photo.jpg"
```

---

## Why this doc was updated

Previous documentation described authentication as active globally. The codebase currently exposes routes without auth enforcement. This file now reflects the real runtime behavior to avoid deployment misunderstandings.

