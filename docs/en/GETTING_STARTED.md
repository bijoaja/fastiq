# Getting Started with FastIQ

> **Language:** English | [Indonesian](../id/GETTING_STARTED.md)

Installation, running the application, and environment configuration guide.

---

## 1. System Requirements

To run this project locally, ensure you have the following tools installed:
* **Python 3.12** or later
* **uv** (recommended package manager). If not yet installed, run:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Docker & Docker Compose** (if you want to run with containers)
* **PostgreSQL 17** (if running locally without Docker)

---

## 2. Local Installation & Setup

Follow these steps to start development locally:

1. **Clone this repository:**
   ```bash
   git clone <repository_url> fastiq
   cd fastiq
   ```

2. **Copy the environment configuration file:**
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies and create Virtual Environment using `uv`:**
   ```bash
   uv sync
   ```
   This command will automatically detect the appropriate Python version, create a `.venv` folder, and install all dependencies listed in `pyproject.toml` and `uv.lock`.

4. **Configure Local Database:**
   Ensure PostgreSQL server is running and create a database named `fastiq`. Adjust the `DATABASE_URL` variable in your `.env` file if needed. Default value:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastiq
   ```

5. **Run Database Migrations:**
   Apply the table structure to the local database using Alembic:
   ```bash
   uv run alembic upgrade head
   ```

6. **Run Seeder (Optional):**
   Populate the database with initial/dummy data (e.g., an initial user):
   ```bash
   uv run python app/scripts/seed.py
   ```

---

## 3. Running the Application

### Running Locally
Start the development server using Uvicorn with the `--reload` flag:
```bash
uv run uvicorn app.main:app --reload --port 8000
```
The application will run at http://localhost:8000. Interactive API documentation is available at:
* **Swagger UI (OpenAPI):** http://localhost:8000/docs
* **ReDoc:** http://localhost:8000/redoc

### Running with Docker

FastIQ provides ready-to-use Docker configurations for development and production:

#### A. Development Mode (Hot Reload & Live Volumemount)
Run the API with PostgreSQL using hot reload configuration (local code changes are immediately reflected in the container):
```bash
docker compose -f docker-compose.dev.yml up --build
```
* API runs on port `8000`.
* Postgres database runs on port `5432` with a local volume for data persistence.

#### B. Production Mode
Run the API in production mode (using optimized multi-stage build, running as non-root user, and including automatic health checks):
```bash
docker compose -f docker-compose.yml up --build
```

---

## 4. Environment Variables

The following environment variables are supported by FastIQ (defined in `.env` or read from OS environment):

| Variable Name | Description | Default |
|---|---|---|
| `APP_NAME` | Application name displayed in Swagger docs. | `FastIQ` |
| `APP_ENV` | Application environment mode (`local`, `development`, `production`). | `local` |
| `DEBUG` | Enable debug mode (show detailed errors in API responses). | `true` |
| `PORT` | Port where FastAPI application runs. | `8000` |
| `DATABASE_URL` | SQLAlchemy database connection string (must be async). | `postgresql+asyncpg://...` |
| `SECRET_KEY` | Secret key used for JWT and cryptographic operations. | `super-secret-key-change-me` |
| `JWT_ALGORITHM` | Algorithm used for JWT encryption. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token expiration time in minutes. | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token expiration time in days. | `7` |
