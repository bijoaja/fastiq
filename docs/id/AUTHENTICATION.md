# Autentikasi & Keamanan (JWT Auth)

> **Bahasa:** Indonesia | [English](../en/AUTHENTICATION.md)

FastIQ mengimplementasikan sistem autentikasi berbasis JWT (JSON Web Token) dengan menggunakan pasangan Access Token (jangka pendek) dan Refresh Token (jangka panjang yang disimpan di database secara terenkripsi menggunakan SHA-256).

---

## 1. Endpoints Autentikasi

Semua API endpoint autentikasi berada di bawah prefix `/api/auth`:

1. **Register User Baru**
   * **Endpoint:** `POST /api/auth/register`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword",
       "name": "John Doe"
     }
     ```
   * **Response:** Mengembalikan data user yang berhasil didaftarkan (`UserResponse`) terbungkus dalam `ApiResponse`.

2. **Login / Dapatkan Token**
   * **Endpoint:** `POST /api/auth/login`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword"
     }
     ```
   * **Response:** Mengembalikan `access_token`, `refresh_token`, `token_type`, dan `expires_in` terbungkus dalam `ApiResponse`.

3. **Refresh Access Token**
   * **Endpoint:** `POST /api/auth/refresh`
   * **Request Body:**
     ```json
     {
       "refresh_token": "string_refresh_token_di_sini"
     }
     ```
   * **Response:** Mengembalikan `access_token` baru beserta `refresh_token` baru (token rotation).

4. **Logout**
   * **Endpoint:** `POST /api/auth/logout`
   * **Request Body:**
     ```json
     {
       "refresh_token": "string_refresh_token_di_sini"
     }
     ```
   * **Response:** Merevokasi refresh token tersebut di database.

5. **Get Profil Saya (Protected)**
   * **Endpoint:** `GET /api/users/me`
   * **Header:** `Authorization: Bearer <access_token>`
   * **Response:** Mengembalikan profil user yang sedang login.

---

## 2. Pola Proteksi Route (Protected Routes)

Untuk mengamankan route tertentu agar hanya dapat diakses oleh user yang telah terautentikasi, gunakan dependency `get_current_user` di level router:

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

Jika token tidak dilampirkan, salah, atau kedaluwarsa, endpoint secara otomatis mengembalikan HTTP 401 (`UnauthorizedException`) dengan format response error terstandar:

```json
{
  "success": false,
  "message": "Invalid or expired token",
  "errors": []
}
```
