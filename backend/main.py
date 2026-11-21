import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import AuthenticatedUser, get_current_user, require_admin

app = FastAPI(title="Technical Support Assistant")
load_dotenv(Path(__file__).parent / ".env")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/me")
def auth_me(user: AuthenticatedUser = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "role": user.role}


@app.get("/admin/check")
def admin_check(user: AuthenticatedUser = Depends(require_admin)):
    return {"id": str(user.id), "role": user.role}
