# Local Development

## Backend

Use the project virtual environment interpreter:

```powershell
E:\AI\backend\.venv\Scripts\python.exe
```

Install dependencies:

```powershell
cd E:\AI\backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run the backend:

```powershell
cd E:\AI\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health endpoint:

```text
GET http://127.0.0.1:8000/api/v1/health
```

The root-level `/health` endpoint is not currently implemented.

Run backend checks:

```powershell
cd E:\AI\backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

## Frontend

Install dependencies:

```powershell
cd E:\AI\frontend
npm install
```

Run the frontend:

```powershell
cd E:\AI\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Run frontend checks:

```powershell
cd E:\AI\frontend
npm run lint
npm test
npm run build
```

## Environment Files

Copy the examples before configuring local services:

```powershell
Copy-Item E:\AI\.env.example E:\AI\.env
Copy-Item E:\AI\backend\.env.example E:\AI\backend\.env
Copy-Item E:\AI\frontend\.env.example E:\AI\frontend\.env
```

Supabase and AI provider values are placeholders until the relevant milestones begin.

Only commit `.env.example` files. Actual `.env` files are ignored by git and
must contain local or deployment-specific values only.

Set `VITE_ADMIN_EMAILS` to a comma-separated list of admin/test-operator email
addresses if you need to see the frontend system diagnostics panel.

## Production Smoke Check

After deployment, run:

```powershell
.\scripts\production-smoke.ps1 -FrontendUrl https://your-frontend.vercel.app -BackendUrl https://your-backend.onrender.com
```

See `docs/PRODUCTION_SMOKE_TEST.md` for the full manual checklist.
