## Run locally

Requirements: Python 3.13 and Node.js 22.

### First-time setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Create `backend/.env` using `backend/.env.example` as a template.
Add your API key locally. Never commit the real `.env`.

### Start the backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Health check: http://127.0.0.1:8000/health

### Start the frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Website: http://localhost:3000

## Automated checks

GitHub Actions checks backend dependencies and Python syntax,
then runs frontend linting and a production build.
These checks do not make paid Claude requests.