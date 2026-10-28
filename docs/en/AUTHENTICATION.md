# Authentication & Security (JWT Auth)

> **Language:** English | [Indonesian](../id/AUTHENTICATION.md)

FastIQ implements JWT (JSON Web Token) based authentication using a pair of Access Token (short-lived) and Refresh Token (long-lived, stored in database encrypted with SHA-256).

---

## 1. Authentication Endpoints

All authentication API endpoints are under the `/api/auth` prefix:

1. **Register New User**
   * **Endpoint:** `POST /api/auth/register`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword",
       "name": "John Doe"
     }
     ```
   * **Response:** Returns the newly registered user data (`UserResponse`) wrapped in `ApiResponse`.

2. **Login / Get Token**
   * **Endpoint:** `POST /api/auth/login`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword"
     }
     ```
   * **Response:** Returns `access_token`, `refresh_token`, `token_type`, and `expires_in` wrapped in `ApiResponse`.

3. **Refresh Access Token**
   * **Endpoint:** `POST /api/auth/refresh`
   * **Request Body:**
     ```json
     {
       "refresh_token": "your_refresh_token_here"
     }
     ```
   * **Response:** Returns new `access_token` and new `refresh_token` (token rotation).

4. **Logout**
   * **Endpoint:** `POST /api/auth/logout`
   * **Request Body:**
     ```json
     {
       "refresh_token": "your_refresh_token_here"
     }
     ```
   * **Response:** Revokes the refresh token in the database.

5. **Get My Profile (Protected)**
   * **Endpoint:** `GET /api/users/me`
   * **Header:** `Authorization: Bearer <access_token>`
   * **Response:** Returns the current logged-in user's profile.

---

## 2. Protected Route Pattern

To secure certain routes so they can only be accessed by authenticated users, use the `get_current_user` dependency at the router level:

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/features")

@router.get("/protected-endpoint")
async def my_protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"message": f"Hello, {current_user.name}"}
```

If a token is not provided, invalid, or expired, the endpoint automatically returns HTTP 401 (`UnauthorizedException`) with standardized error response format:

```json
{
  "success": false,
  "message": "Invalid or expired token",
  "errors": []
}
```
