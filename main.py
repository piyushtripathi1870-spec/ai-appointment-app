import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import router as api_router
from app.db import init_db, SessionLocal
from app.models import Company

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="AI Appointment Scheduler API")

# Enable CORS so our frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def custom_domain_middleware(request: Request, call_next):
    host = request.headers.get("host")
    if host:
        db = SessionLocal()
        try:
            company = db.query(Company).filter(Company.custom_domain == host).first()
            if company:
                request.state.company_id = company.id
        finally:
            db.close()

    response = await call_next(request)
    return response

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include our API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api")
def api_root():
    return {"message": "Welcome to the AI Appointment Scheduler API! Use /api/signup or /api/login to start."}

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
