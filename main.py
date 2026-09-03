import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import router as api_router
from app.db import init_db, SessionLocal
from app.models import Company

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIR = PUBLIC_DIR if os.path.isdir(PUBLIC_DIR) else STATIC_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Appointment Scheduler API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def custom_domain_middleware(request: Request, call_next):
    host = request.headers.get("host")
    if host:
        try:
            db = SessionLocal()
            try:
                company = db.query(Company).filter(Company.custom_domain == host).first()
                if company:
                    request.state.company_id = company.id
            finally:
                db.close()
        except Exception:
            pass

    return await call_next(request)


app.include_router(api_router, prefix="/api")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api")
def api_root():
    return {"message": "Welcome to the AI Appointment Scheduler API! Use /api/signup or /api/login to start."}


@app.get("/health")
def health():
    return {"status": "ok"}


# Local dev only — Vercel serves files from public/ automatically
if not os.getenv("VERCEL"):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
