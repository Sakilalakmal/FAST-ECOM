# FAST Ecom Backend Foundation

Minimal production-style FastAPI foundation for the first phase of the e-commerce backend.

## Stack

- Python
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- Pydantic Settings
- Uvicorn

## Project Structure

```text
backend/
  app/
    api/
      v1/
        endpoints/
          health.py
          sample.py
        router.py
    core/
      config.py
    db/
      base.py
      session.py
    models/
    schemas/
    repositories/
    services/
    dependencies/
    middleware/
    utils/
    main.py
  alembic/
  alembic.ini
  tests/
  .env.example
  .gitignore
  requirements.txt
```

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create your environment file

```powershell
Copy-Item .env.example .env
```

Update the PostgreSQL values in `.env` if needed.

## Environment Variables

Required database settings:

- `POSTGRES_SERVER`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

Optional:

- `DATABASE_URL`
- `PROJECT_NAME`
- `APP_ENV`
- `DEBUG`
- `API_V1_STR`

If `DATABASE_URL` is set, it takes precedence over the individual PostgreSQL fields.

## Run the Application

From the `backend/` directory:

```powershell
uvicorn app.main:app --reload
```

Application URLs:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`
- Sample route: `http://127.0.0.1:8000/api/v1/sample/ping`

## Alembic Commands

Create a new migration:

```powershell
alembic revision --autogenerate -m "init"
```

Apply migrations:

```powershell
alembic upgrade head
```

Rollback the latest migration:

```powershell
alembic downgrade -1
```

## Notes for the Next Phase

- Add SQLAlchemy models under `app/models/`
- Import model modules before Alembic autogeneration when models are introduced
- Keep business logic in `services/` and data access in `repositories/`
- Add reusable dependencies to `dependencies/`
