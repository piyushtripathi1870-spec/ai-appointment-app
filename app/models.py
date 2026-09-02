from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(enum.Enum):
    OWNER = "owner"
    CLIENT = "client"

class SubscriptionTier(enum.Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    brand_color = Column(String, nullable=True, default="#2563eb")
    description = Column(String, nullable=True)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.STARTER, nullable=False)
    custom_domain = Column(String, unique=True, nullable=True)

    users = relationship("User", back_populates="company")
    appointments = relationship("Appointment", back_populates="company")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    company_id = Column(String, ForeignKey("companies.id"), index=True, nullable=True)

    appointments = relationship("Appointment", back_populates="customer")
    company = relationship("Company", back_populates="users")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), index=True, nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('company_id', 'appointment_time', name='uq_company_appointment_time'),
    )

    customer = relationship("User", back_populates="appointments")
    company = relationship("Company", back_populates="appointments")
