import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from database.connection import Base

def generate_uuid():
    return str(uuid.uuid4())

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=False)
    phone_hash = Column(String(64), nullable=False, index=True)
    household_id = Column(String(64), nullable=False, index=True)
    dob = Column(String(10), nullable=True) # YYYY-MM-DD
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True) # MALE, FEMALE, OTHER
    caste_category = Column(String(50), nullable=True) # OPEN, OBC, SC, ST, VJNT, EWS, SEBC
    annual_income = Column(Float, nullable=True)
    landholding_acres = Column(Float, nullable=True, default=0.0)
    occupation = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=False, default="Maharashtra")
    has_disability = Column(Boolean, default=False)
    is_student = Column(Boolean, default=False)
    education_level = Column(String(100), nullable=True)
    consent_granted = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("CitizenDocument", back_populates="citizen", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="citizen", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="citizen", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="citizen", cascade="all, delete-orphan")

class CitizenDocument(Base):
    __tablename__ = "citizen_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False) # IDENTITY, INCOME, CASTE, LAND, AFFIDAVIT
    file_path = Column(String(500), nullable=False)
    compressed_path = Column(String(500), nullable=True)
    ocr_data = Column(JSON, nullable=True)
    blur_score = Column(Float, nullable=True)
    quality_status = Column(String(20), default="PENDING") # PASS, FAIL
    validation_status = Column(String(50), default="PENDING") # VALID, EXPIRED, MISMATCH
    validation_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    citizen = relationship("Citizen", back_populates="documents")

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String(100), primary_key=True) # slug e.g. pm_kisan
    scheme_code = Column(String(100), unique=True, nullable=False, index=True)
    scheme_name = Column(String(255), nullable=False)
    scheme_name_mr = Column(String(255), nullable=True)
    department = Column(String(255), nullable=False)
    target_beneficiary = Column(String(255), nullable=False)
    benefit_amount = Column(Float, nullable=False)
    benefit_type = Column(String(100), nullable=False) # DIRECT_BENEFIT_TRANSFER, TUITION_WAIVER, SUBSIDY, PENSION
    sla_days = Column(Integer, default=30)
    ast_rule = Column(JSON, nullable=False)
    citations = Column(JSON, nullable=True)
    mutual_exclusions = Column(JSON, default=list) # List of scheme IDs that cannot be co-claimed
    dom_mapping_key = Column(String(100), nullable=True) # mahadbt_post_matric, pmkisan_registration
    status = Column(String(50), default="DRAFT_HITL", index=True) # DRAFT_HITL, ACTIVE, DEPRECATED
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="scheme")
    audit_logs = relationship("AuditLog", back_populates="scheme")

class SchemeVersionDiff(Base):
    __tablename__ = "scheme_version_diffs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scheme_id = Column(String(100), nullable=False, index=True)
    old_version = Column(Integer, nullable=False)
    new_version = Column(Integer, nullable=False)
    ast_diff = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(String(100), ForeignKey("schemes.id"), nullable=False, index=True)
    application_status = Column(String(50), default="SUBMITTED", index=True) # DRAFT, SUBMITTED, IN_REVIEW, APPROVED, REJECTED, BREACHED
    portal_tracking_id = Column(String(100), nullable=True, index=True)
    submission_receipt_path = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    sla_deadline = Column(DateTime, nullable=True)
    days_elapsed = Column(Integer, default=0)
    grievance_filed = Column(Boolean, default=False)
    audit_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    citizen = relationship("Citizen", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(String(100), ForeignKey("schemes.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False) # EVALUATION, PURGE, APPLICATION_SUBMISSION
    input_snapshot = Column(JSON, nullable=True)
    rule_evaluated = Column(JSON, nullable=True)
    verdict = Column(String(50), nullable=False) # ELIGIBLE, NEAR_MISS, INELIGIBLE, PURGED
    decision_signature = Column(String(64), nullable=False, index=True) # SHA-256
    timestamp = Column(DateTime, default=datetime.utcnow)

    citizen = relationship("Citizen", back_populates="audit_logs")
    scheme = relationship("Scheme", back_populates="audit_logs")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), default="WHATSAPP") # WHATSAPP, SMS, IN_APP
    message = Column(Text, nullable=False)
    status = Column(String(50), default="SIMULATED") # QUEUED, SENT, SIMULATED
    sent_at = Column(DateTime, default=datetime.utcnow)

    citizen = relationship("Citizen", back_populates="notifications")
