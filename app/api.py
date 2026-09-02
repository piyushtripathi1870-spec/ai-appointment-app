from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .db import get_db
from .models import User, Appointment, UserRole, Company, SubscriptionTier
from .auth import verify_password, get_password_hash, create_access_token, decode_access_token
from .scheduler import AppointmentScheduler

router = APIRouter()
scheduler = AppointmentScheduler()
security = HTTPBearer()

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str
    company_id: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    role: UserRole
    company_id: Optional[str] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BookingRequest(BaseModel):
    text: str

# --- Auth Dependencies ---
def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = auth.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def check_tier_limits(company: Company, db: Session):
    if company.subscription_tier == SubscriptionTier.STARTER:
        # Count appointments for the current calendar month
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = db.query(Appointment).filter(
            Appointment.company_id == company.id,
            Appointment.appointment_time >= first_day
        ).count()
        if count >= 50:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly appointment limit reached for Starter tier. Please upgrade your plan."
            )

# --- Endpoints ---

@router.get("/company/{company_id}")
def get_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "id": company.id,
        "name": company.name,
        "logo_url": company.logo_url,
        "brand_color": company.brand_color,
        "description": company.description,
        "subscription_tier": company.subscription_tier.value,
        "custom_domain": company.custom_domain
    }

@router.put("/company/{company_id}")
def update_company(company_id: str, update_data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.OWNER or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Only the company owner can update branding")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for key, value in update_data.items():
        if hasattr(company, key):
            setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return {"message": "Company profile updated successfully"}

@router.patch("/company/{company_id}/subscription")
def update_subscription(company_id: str, tier: SubscriptionTier, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.OWNER or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Only the company owner can update the subscription plan")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.subscription_tier = tier
    db.commit()
    db.refresh(company)
    return {"message": f"Subscription updated to {tier.value} successfully"}

@router.patch("/company/{company_id}/domain")
def update_custom_domain(company_id: str, domain: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.OWNER or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Only the company owner can update the custom domain")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.subscription_tier != SubscriptionTier.ENTERPRISE:
        raise HTTPException(
            status_code=403,
            detail="Custom domains are only available for Enterprise tier users."
        )

    company.custom_domain = domain
    db.commit()
    db.refresh(company)
    return {"message": "Custom domain updated successfully"}

@router.post("/signup", response_model=UserOut)

def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd, role=UserRole.CLIENT, company_id=user.company_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/book")
def book_appointment(request: Request, booking_request: BookingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business owners cannot book appointments for themselves."
        )

    # Prioritize custom domain resolved company_id, then fallback to DEFAULT_COMPANY
    company_id = getattr(request.state, "company_id", "DEFAULT_COMPANY")

    # Enforce tier limits
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    check_tier_limits(company, db)

    response = scheduler.process_request(db, booking_request.text, user.id, company_id)
    return {"response": response}

@router.get("/dashboard")
def get_dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Determine which company we are viewing (Custom domain or User's company)
    company_id = getattr(request.state, "company_id", user.company_id)
    if not company_id:
        company_id = "DEFAULT_COMPANY"

    if user.role == UserRole.OWNER:
        # Owner sees all for their company (or the resolved custom domain company)
        data = scheduler.list_appointments(db, company_id=company_id)
    else:
        # Client sees only their own
        data = scheduler.list_appointments(db, customer_id=user.id)

    # Fetch company branding
    company = db.query(Company).filter(Company.id == company_id).first()
    company_info = {
        "id": company.id if company else company_id,
        "name": company.name if company else "Default Business",
        "logo_url": company.logo_url if company else None,
        "brand_color": company.brand_color if company else "#2563eb",
        "description": company.description if company else None,
        "subscription_tier": company.subscription_tier.value if company else "starter",
    }

    return {"role": user.role, "data": data, "company": company_info}

