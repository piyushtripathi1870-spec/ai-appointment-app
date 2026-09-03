from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .models import Base
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_database_url():
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Vercel's filesystem is read-only except /tmp
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/appointments.db"

    return f"sqlite:///{os.path.join(BASE_DIR, 'appointments.db')}"


SQLALCHEMY_DATABASE_URL = _resolve_database_url()

_engine_kwargs = {}
_connect_args = {}

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    _connect_args = {"check_same_thread": False}
else:
    _engine_kwargs = {"poolclass": NullPool, "pool_pre_ping": True}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=_connect_args,
    **_engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from .models import Company

        if not db.query(Company).filter(Company.id == "DEFAULT_COMPANY").first():
            default_company = Company(
                id="DEFAULT_COMPANY",
                name="Default Service Business",
                brand_color="#2563eb",
            )
            db.add(default_company)
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
