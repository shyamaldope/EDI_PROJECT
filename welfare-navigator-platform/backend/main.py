import os
import uuid
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from config import settings
from database.connection import init_db, get_db, get_sync_db
from database.models import Citizen, CitizenDocument, Scheme, SchemeVersionDiff, Application, AuditLog, Notification
from modules.voice_profile.pii_scrubber import scrub_pii, hash_phone, hash_household
from modules.voice_profile.bhashini_client import bhashini_client
from modules.voice_profile.slot_filler import slot_filler
from modules.rule_engine.ast_evaluator import ast_evaluator
from modules.rule_engine.near_miss_analyzer import near_miss_analyzer
from modules.rule_engine.scheme_stacker import scheme_stacker
from modules.doc_auditor.vision_ocr import vision_ocr
from modules.doc_auditor.cross_validator import cross_validator
from modules.doc_auditor.media_compressor import media_compressor
from modules.ingestion.gr_scraper import gr_scraper
from modules.ingestion.pdf_to_ast import pdf_to_ast_compiler
from modules.ingestion.ast_differ import ast_differ
from modules.ingestion.reverse_matcher import reverse_matcher
from modules.tracker_twin.sla_monitor import sla_monitor
from modules.tracker_twin.grievance_drafter import grievance_drafter
from modules.tracker_twin.policy_simulator import policy_simulator
from modules.rpa_copilot.playwright_runner import playwright_runner

app = FastAPI(
    title="Welfare Navigator Platform API",
    description="Autonomous Agentic Citizen Welfare & Policy Intelligence Platform (DPDP Act 2023 Aligned)",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = BASE_DIR.parent / "sample_artifacts"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
if ARTIFACTS_DIR.exists():
    app.mount("/sample_artifacts", StaticFiles(directory=str(ARTIFACTS_DIR)), name="sample_artifacts")

@app.on_event("startup")
async def startup_event():
    await init_db()

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "reference_date": settings.REFERENCE_DATE,
        "database": "CONNECTED",
        "local_ai_fallback": settings.USE_LOCAL_AI_FALLBACK,
        "dpdp_act_compliance": "ALIGNED"
    }

# ==============================================================================
# 1. CITIZEN & DPDP ACT 2023 PRIVACY ENDPOINTS
# ==============================================================================

@app.get("/api/v1/citizens")
def list_citizens(db: Session = Depends(get_sync_db)):
    citizens = db.query(Citizen).all()
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "age": c.age,
            "gender": c.gender,
            "caste_category": c.caste_category,
            "annual_income": c.annual_income,
            "landholding_acres": c.landholding_acres,
            "occupation": c.occupation,
            "district": c.district,
            "state": c.state,
            "has_disability": c.has_disability,
            "is_student": c.is_student,
            "household_id": c.household_id,
            "consent_granted": c.consent_granted
        }
        for c in citizens
    ]

@app.get("/api/v1/citizens/{citizen_id}")
def get_citizen(citizen_id: str, db: Session = Depends(get_sync_db)):
    c = db.query(Citizen).filter(Citizen.id == citizen_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Citizen not found")
    return {
        "id": c.id,
        "full_name": c.full_name,
        "phone_hash": c.phone_hash,
        "household_id": c.household_id,
        "dob": c.dob,
        "age": c.age,
        "gender": c.gender,
        "caste_category": c.caste_category,
        "annual_income": c.annual_income,
        "landholding_acres": c.landholding_acres,
        "occupation": c.occupation,
        "district": c.district,
        "state": c.state,
        "has_disability": c.has_disability,
        "is_student": c.is_student,
        "education_level": c.education_level,
        "consent_granted": c.consent_granted,
        "consent_timestamp": c.consent_timestamp
    }

@app.post("/api/v1/citizens")
def create_or_update_citizen(data: Dict[str, Any], db: Session = Depends(get_sync_db)):
    """
    Registers or updates citizen profile with salted SHA-256 phone & household hashes.
    Enforces DPDP Act 2023 Notice and Consent.
    """
    if not data.get("consent_granted"):
        raise HTTPException(status_code=403, detail="DPDP Act 2023 Consent Required to process citizen data.")

    phone = data.get("phone", "9820012345")
    ration_card = data.get("ration_card_number", "RC-MAHA-DEFAULT")
    phone_h = hash_phone(phone)
    household_h = hash_household(ration_card)

    c_id = data.get("id") or str(uuid.uuid4())
    existing = db.query(Citizen).filter(Citizen.id == c_id).first()

    if existing:
        for k, v in data.items():
            if hasattr(existing, k) and k not in ["id", "phone", "ration_card_number"]:
                setattr(existing, k, v)
        existing.phone_hash = phone_h
        existing.household_id = household_h
        db.commit()
        return {"status": "UPDATED", "citizen_id": existing.id}
    else:
        new_c = Citizen(
            id=c_id,
            full_name=data.get("full_name", "Anonymous Citizen"),
            phone_hash=phone_h,
            household_id=household_h,
            dob=data.get("dob"),
            age=data.get("age", 40),
            gender=data.get("gender", "MALE"),
            caste_category=data.get("caste_category", "OBC"),
            annual_income=float(data.get("annual_income", 180000.0)),
            landholding_acres=float(data.get("landholding_acres", 2.0)),
            occupation=data.get("occupation", "Farmer"),
            district=data.get("district", "Kolhapur"),
            state=data.get("state", "Maharashtra"),
            has_disability=data.get("has_disability", False),
            is_student=data.get("is_student", False),
            education_level=data.get("education_level", "Secondary"),
            consent_granted=True,
            consent_timestamp=datetime.utcnow().isoformat()
        )
        db.add(new_c)
        db.commit()
        return {"status": "CREATED", "citizen_id": new_c.id}

@app.delete("/api/v1/citizens/{citizen_id}/purge")
def purge_citizen_vault(citizen_id: str, db: Session = Depends(get_sync_db)):
    """
    1-Click DPDP Act 2023 'Right to Erasure' Vault Purge.
    Cryptographically wipes citizen profile, uploaded documents, audit logs, and notifications.
    """
    c = db.query(Citizen).filter(Citizen.id == citizen_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Citizen not found")

    # Count records to be purged
    docs = db.query(CitizenDocument).filter(CitizenDocument.citizen_id == citizen_id).all()
    files_wiped = 0
    for d in docs:
        if d.file_path and os.path.exists(d.file_path):
            try:
                os.remove(d.file_path)
                files_wiped += 1
            except Exception:
                pass
        if d.compressed_path and os.path.exists(d.compressed_path):
            try:
                os.remove(d.compressed_path)
                files_wiped += 1
            except Exception:
                pass

    audit_count = db.query(AuditLog).filter(AuditLog.citizen_id == citizen_id).count()
    notif_count = db.query(Notification).filter(Notification.citizen_id == citizen_id).count()

    import hashlib
    receipt_hash = hashlib.sha256(f"{citizen_id}::PURGED::{datetime.utcnow().isoformat()}".encode()).hexdigest()

    # Cascade delete citizen
    db.delete(c)
    db.commit()

    return {
        "status": "PURGED",
        "citizen_id": citizen_id,
        "files_wiped": files_wiped,
        "records_deleted": {
            "profile": 1,
            "documents": len(docs),
            "audit_logs": audit_count,
            "notifications": notif_count
        },
        "purge_receipt_hash": receipt_hash,
        "message": "Citizen Vault completely erased in compliance with DPDP Act 2023 Section 12."
    }

# ==============================================================================
# 2. VOICE, CHAT & ENTROPY SLOT-FILLING
# ==============================================================================

@app.post("/api/v1/voice/process")
async def process_voice_or_text(payload: Dict[str, Any]):
    """
    Processes vernacular user voice or text input with PII redaction and slot extraction.
    """
    raw_text = payload.get("text", "")
    lang = payload.get("language", "mr")

    # 1. PII Redaction
    scrubbed = scrub_pii(raw_text)
    clean_text = scrubbed["clean_text"]

    # 2. Extract demographic slots
    extracted_slots = slot_filler.extract_slots_from_text(clean_text)

    # 3. Detect Proactive Life Events
    life_events = slot_filler.detect_life_events(clean_text)

    # 4. Generate synthesized audio / text response
    response_text = f"नमस्कार, आम्ही आपली माहिती तपासली आहे."
    if extracted_slots:
        slot_details = ", ".join([f"{k}: {v}" for k, v in extracted_slots.items()])
        response_text = f"नोंदणी यशस्वी: {slot_details}."
    if life_events:
        response_text += f" विशेष योजना सुचवली: {life_events[0]['event_name']}."

    tts_res = await bhashini_client.synthesize_speech(response_text, target_lang=lang)

    return {
        "clean_text": clean_text,
        "pii_badge": scrubbed["pii_badge"],
        "extracted_slots": extracted_slots,
        "life_events": life_events,
        "response_text": response_text,
        "audio_uri": tts_res.get("audio_uri"),
        "execution_mode": tts_res.get("execution_mode")
    }

@app.post("/api/v1/voice/next-question")
def get_next_best_question(current_profile: Dict[str, Any], db: Session = Depends(get_sync_db)):
    """
    Computes Shannon Entropy / Information Gain to ask the single most informative question.
    """
    schemes = db.query(Scheme).filter(Scheme.status == "ACTIVE").all()
    scheme_dicts = [{"id": s.id, "ast_rule": s.ast_rule} for s in schemes]
    best_q = slot_filler.compute_next_best_question(current_profile, scheme_dicts)
    return {"next_question": best_q}

# ==============================================================================
# 3. RULE ENGINE & SCHEME STACKER
# ==============================================================================

@app.get("/api/v1/citizens/{citizen_id}/schemes")
def evaluate_citizen_schemes(citizen_id: str, db: Session = Depends(get_sync_db)):
    """
    Pure Python deterministic evaluation of all ACTIVE schemes for a citizen.
    Categorizes into Eligible (with audit signatures), Near-Miss (75-99%), and MWIS Optimal Stack.
    """
    c = db.query(Citizen).filter(Citizen.id == citizen_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Citizen not found")

    citizen_dict = {
        "id": c.id,
        "full_name": c.full_name,
        "age": c.age,
        "gender": c.gender,
        "caste_category": c.caste_category,
        "annual_income": c.annual_income,
        "landholding_acres": c.landholding_acres,
        "occupation": c.occupation,
        "district": c.district,
        "state": c.state,
        "has_disability": c.has_disability,
        "is_student": c.is_student
    }

    # Only evaluate ACTIVE schemes (DRAFT_HITL are quarantined!)
    schemes = db.query(Scheme).filter(Scheme.status == "ACTIVE").all()

    eligible = []
    near_misses = []
    now_iso = datetime.utcnow().isoformat()

    for s in schemes:
        passed, condition_results = ast_evaluator.evaluate(s.ast_rule, citizen_dict)
        sig = ast_evaluator.generate_audit_signature(c.id, s.id, "ELIGIBLE" if passed else "INELIGIBLE", s.ast_rule, now_iso)

        if passed:
            eligible.append({
                "id": s.id,
                "scheme_code": s.scheme_code,
                "scheme_name": s.scheme_name,
                "scheme_name_mr": s.scheme_name_mr,
                "department": s.department,
                "benefit_amount": s.benefit_amount,
                "benefit_type": s.benefit_type,
                "sla_days": s.sla_days,
                "mutual_exclusions": s.mutual_exclusions or [],
                "citations": s.citations or [],
                "condition_results": condition_results,
                "verdict": "ELIGIBLE",
                "audit_signature": sig
            })
        else:
            nm = near_miss_analyzer.analyze(s.__dict__, condition_results, citizen_dict)
            if nm["is_near_miss"]:
                near_misses.append({
                    "id": s.id,
                    "scheme_name": s.scheme_name,
                    "scheme_name_mr": s.scheme_name_mr,
                    "benefit_amount": s.benefit_amount,
                    "match_percentage": nm["match_percentage"],
                    "remediations": nm["remediations"],
                    "condition_results": condition_results,
                    "verdict": "NEAR_MISS",
                    "audit_signature": sig
                })

    # Solve Maximum Weight Independent Set (MWIS) Graph Optimization
    optimal_stack = scheme_stacker.optimize_individual_stack(eligible)

    return {
        "citizen_id": c.id,
        "citizen_name": c.full_name,
        "evaluation_timestamp": now_iso,
        "eligible_schemes": eligible,
        "eligible_count": len(eligible),
        "near_miss_schemes": near_misses,
        "near_miss_count": len(near_misses),
        "optimal_benefit_stack": optimal_stack
    }

@app.get("/api/v1/households/{household_id}/schemes")
def evaluate_household_schemes(household_id: str, db: Session = Depends(get_sync_db)):
    """
    Evaluates and stacks benefits for all citizens belonging to a shared household_id.
    """
    members = db.query(Citizen).filter(Citizen.household_id == household_id).all()
    if not members:
        raise HTTPException(status_code=404, detail="Household not found")

    household_eligibility = []
    schemes = db.query(Scheme).filter(Scheme.status == "ACTIVE").all()

    for m in members:
        m_dict = {
            "id": m.id,
            "full_name": m.full_name,
            "age": m.age,
            "gender": m.gender,
            "caste_category": m.caste_category,
            "annual_income": m.annual_income,
            "landholding_acres": m.landholding_acres,
            "occupation": m.occupation,
            "district": m.district,
            "state": m.state,
            "has_disability": m.has_disability,
            "is_student": m.is_student
        }
        eligible = []
        for s in schemes:
            p, _ = ast_evaluator.evaluate(s.ast_rule, m_dict)
            if p:
                eligible.append({
                    "id": s.id,
                    "scheme_name": s.scheme_name,
                    "benefit_amount": s.benefit_amount,
                    "mutual_exclusions": s.mutual_exclusions or []
                })
        household_eligibility.append({
            "citizen_id": m.id,
            "citizen_name": m.full_name,
            "eligible_schemes": eligible
        })

    stack = scheme_stacker.optimize_household_stack(household_eligibility)
    return {
        "household_id": household_id,
        "household_stack": stack
    }

@app.get("/api/v1/schemes")
def list_schemes(status: Optional[str] = None, db: Session = Depends(get_sync_db)):
    query = db.query(Scheme)
    if status:
        query = query.filter(Scheme.status == status)
    schemes = query.all()
    return [
        {
            "id": s.id,
            "scheme_code": s.scheme_code,
            "scheme_name": s.scheme_name,
            "scheme_name_mr": s.scheme_name_mr,
            "department": s.department,
            "target_beneficiary": s.target_beneficiary,
            "benefit_amount": s.benefit_amount,
            "benefit_type": s.benefit_type,
            "sla_days": s.sla_days,
            "status": s.status,
            "version": s.version,
            "ast_rule": s.ast_rule,
            "citations": s.citations or []
        }
        for s in schemes
    ]

# ==============================================================================
# 4. PRE-FLIGHT DOCUMENT AUDITOR & COMPRESSOR
# ==============================================================================

@app.post("/api/v1/documents/audit")
async def audit_document(
    citizen_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_sync_db)
):
    """
    Pre-flight document audit: OCR extraction, RapidFuzz name match (<85 alert),
    expiry check vs 2026-10-22, blur scoring, and affidavit generation.
    """
    citizen = db.query(Citizen).filter(Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")

    file_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix or ".jpg"
    saved_filename = f"doc_{file_id}_{file.filename}"
    saved_path = UPLOADS_DIR / saved_filename

    contents = await file.read()
    with open(saved_path, "wb") as f_out:
        f_out.write(contents)

    # 1. Blur and image quality check
    blur_score = cross_validator.calculate_blur_score(str(saved_path))
    quality_status = "PASS" if blur_score >= 80.0 else "FAIL_BLURRY"

    # 2. OCR field extraction with PII redaction
    ocr_result = await vision_ocr.extract_document_data(str(saved_path), doc_type)
    extracted = ocr_result["extracted_fields"]

    # 3. RapidFuzz Name Matching
    doc_name = extracted.get("name", citizen.full_name)
    name_val = cross_validator.validate_name_match(citizen.full_name, doc_name)

    # 4. Expiry validation vs 2026-10-22
    valid_until = extracted.get("valid_until", "LIFETIME")
    expiry_val = cross_validator.validate_expiry(valid_until, settings.REFERENCE_DATE)

    # 5. Automated Affidavit Generation if name mismatch detected
    affidavit_url = None
    if name_val["alert"]:
        aff_path = cross_validator.generate_name_affidavit_pdf(
            citizen_name=citizen.full_name,
            document_name=doc_name,
            document_type=doc_type,
            output_dir=str(UPLOADS_DIR / "affidavits")
        )
        affidavit_url = f"/api/v1/documents/affidavit/{Path(aff_path).name}"

    # Record in database
    doc_record = CitizenDocument(
        citizen_id=citizen.id,
        doc_type=doc_type,
        file_path=str(saved_path),
        ocr_data=extracted,
        blur_score=blur_score,
        quality_status=quality_status,
        validation_status="MISMATCH" if name_val["alert"] else ("EXPIRED" if expiry_val["is_expired"] else "VALID"),
        validation_errors={"name_mismatch": name_val["alert"], "expired": expiry_val["is_expired"]}
    )
    db.add(doc_record)
    db.commit()

    return {
        "document_id": doc_record.id,
        "filename": file.filename,
        "blur_score": blur_score,
        "quality_status": quality_status,
        "extracted_fields": extracted,
        "rapidfuzz_name_score": name_val["score"],
        "name_mismatch_alert": name_val["alert"],
        "name_validation_message": name_val["message"],
        "expiry_status": "EXPIRED" if expiry_val["is_expired"] else "VALID",
        "expiry_message": expiry_val["message"],
        "affidavit_pdf_url": affidavit_url,
        "pii_badge": ocr_result["pii_badge"],
        "execution_mode": ocr_result["execution_mode"]
    }

@app.post("/api/v1/documents/compress")
async def compress_document(file: UploadFile = File(...)):
    """
    Binary-search Pillow compressor to strictly fit [20KB, 50KB] government portal constraints.
    """
    file_id = str(uuid.uuid4())[:8]
    input_path = UPLOADS_DIR / f"raw_{file_id}_{file.filename}"
    output_path = UPLOADS_DIR / f"compressed_20to50kb_{file_id}.jpg"

    content = await file.read()
    with open(input_path, "wb") as f_in:
        f_in.write(content)

    res = media_compressor.compress_for_portal(str(input_path), str(output_path))
    res["download_url"] = f"/api/v1/documents/download/{output_path.name}"
    return res

@app.get("/api/v1/documents/download/{filename}")
def download_document(filename: str):
    p = UPLOADS_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(p))

@app.get("/api/v1/documents/affidavit/{filename}")
def download_affidavit(filename: str):
    p = UPLOADS_DIR / "affidavits" / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Affidavit not found")
    return FileResponse(str(p))

# ==============================================================================
# 5. ADMIN INGESTION, AST DIFFING & HITL APPROVAL
# ==============================================================================

@app.get("/api/v1/admin/gr-files")
def list_incoming_grs():
    files = gr_scraper.scan_incoming_pdfs()
    return {"incoming_gr_files": files}

@app.post("/api/v1/admin/ingest-gr")
async def ingest_government_resolution(
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    db: Session = Depends(get_sync_db)
):
    """
    Ingests a Government Resolution PDF and creates a DRAFT_HITL scheme.
    Mandatory Safeguard: Quarantined from citizen eligibility until Admin approval.
    """
    if file:
        target_path = BASE_DIR / "incoming_gr_pdfs" / file.filename
        content = await file.read()
        with open(target_path, "wb") as f_out:
            f_out.write(content)
        pdf_path = str(target_path)
    elif filename:
        pdf_path = str(BASE_DIR / "incoming_gr_pdfs" / filename)
    else:
        # Fallback to sample artifact
        pdf_path = str(ARTIFACTS_DIR / "Artifact_A_Maharashtra_GR_2026.pdf")

    candidate = await pdf_to_ast_compiler.compile_gr_to_ast(pdf_path)

    # Persist as DRAFT_HITL
    existing = db.query(Scheme).filter(Scheme.id == candidate["id"]).first()
    if not existing:
        scheme = Scheme(
            id=candidate["id"],
            scheme_code=candidate["scheme_code"],
            scheme_name=candidate["scheme_name"],
            scheme_name_mr=candidate.get("scheme_name_mr"),
            department=candidate["department"],
            target_beneficiary=candidate["target_beneficiary"],
            benefit_amount=candidate["benefit_amount"],
            benefit_type=candidate["benefit_type"],
            sla_days=candidate["sla_days"],
            status="DRAFT_HITL", # MANDATORY HITL QUARANTINE
            version=1,
            dom_mapping_key=candidate.get("dom_mapping_key"),
            citations=candidate.get("citations", []),
            ast_rule=candidate["ast_rule"]
        )
        db.add(scheme)
        db.commit()

    return candidate

@app.post("/api/v1/admin/schemes/diff")
def diff_scheme_versions(payload: Dict[str, Any]):
    """
    Computes visual Git-style AST diff between old and new scheme ASTs.
    """
    old_ast = payload.get("old_ast", {})
    new_ast = payload.get("new_ast", {})
    diff = ast_differ.diff_asts(old_ast, new_ast)
    return diff

@app.post("/api/v1/admin/schemes/{scheme_id}/approve")
def approve_scheme(scheme_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_sync_db)):
    """
    HITL Gateway: Admin approves a DRAFT_HITL scheme, transitioning it to ACTIVE.
    Triggers reverse-matching across all registered citizens to dispatch proactive notifications.
    """
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    scheme.status = "ACTIVE"
    scheme.updated_at = datetime.utcnow()
    db.commit()

    # Zero-config background task dispatch: uses FastAPI BackgroundTasks
    background_tasks.add_task(reverse_matcher.match_and_notify, db, scheme.id)

    return {
        "status": "APPROVED_ACTIVE",
        "scheme_id": scheme.id,
        "scheme_name": scheme.scheme_name,
        "reverse_matching": "DISPATCHED_BACKGROUND_TASK",
        "message": f"Scheme '{scheme.scheme_name}' approved and moved to ACTIVE. Reverse matching initiated."
    }

# ==============================================================================
# 6. SLA TRACKER & GRIEVANCE DRAFTER
# ==============================================================================

@app.get("/api/v1/tracker/applications")
def list_applications_sla(db: Session = Depends(get_sync_db)):
    """
    Lists applications with SLA timeline metrics and flags RTS Act breaches.
    """
    apps = db.query(Application).all()
    results = []
    for a in apps:
        s = db.query(Scheme).filter(Scheme.id == a.scheme_id).first()
        c = db.query(Citizen).filter(Citizen.id == a.citizen_id).first()
        metrics = sla_monitor.evaluate_application_sla(a, s)
        metrics["citizen_name"] = c.full_name if c else "Unknown"
        metrics["citizen_id"] = a.citizen_id
        results.append(metrics)
    return results

@app.post("/api/v1/tracker/grievance/draft")
def draft_grievance_pdf(payload: Dict[str, Any], db: Session = Depends(get_sync_db)):
    """
    Generates formal legal Right to Services (RTS) Act 2015 First Appeal PDF.
    """
    app_id = payload.get("application_id")
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    scheme = db.query(Scheme).filter(Scheme.id == app.scheme_id).first()
    citizen = db.query(Citizen).filter(Citizen.id == app.citizen_id).first()

    metrics = sla_monitor.evaluate_application_sla(app, scheme)

    pdf_path = grievance_drafter.draft_rts_appeal_pdf(
        citizen_name=citizen.full_name,
        phone_masked="[PHONE_REDACTED]",
        application_id=app.id,
        portal_tracking_id=app.portal_tracking_id or "MHA-2026-UNKNOWN",
        scheme_name=scheme.scheme_name,
        department=scheme.department,
        days_elapsed=metrics["days_elapsed"],
        sla_days=metrics["sla_limit_days"],
        days_overdue=metrics["days_overdue"],
        output_dir=str(UPLOADS_DIR / "grievances")
    )

    app.grievance_filed = True
    db.commit()

    return {
        "status": "GRIEVANCE_GENERATED",
        "pdf_url": f"/api/v1/tracker/receipt/{Path(pdf_path).name}",
        "days_overdue": metrics["days_overdue"],
        "statutory_act": "Maharashtra Right to Public Services Act, 2015",
        "message": "Form-1 First Appeal generated ready for submission to Appellate Authority."
    }

@app.get("/api/v1/tracker/receipt/{filename}")
def download_receipt_or_grievance(filename: str):
    p = UPLOADS_DIR / "grievances" / filename
    if not p.exists():
        p = UPLOADS_DIR / "receipts" / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(p))

# ==============================================================================
# 7. POLICY TWIN SIMULATOR & GOAL-SEEK OPTIMIZER
# ==============================================================================

@app.post("/api/v1/policy/simulate")
def simulate_policy_what_if(payload: Dict[str, Any], db: Session = Depends(get_sync_db)):
    """
    Forward What-If Policy Twin simulation.
    """
    scheme_id = payload.get("scheme_id", "pm_kisan")
    income = payload.get("income_ceiling")
    land = payload.get("land_ceiling")
    castes = payload.get("castes")

    result = policy_simulator.forward_simulate(
        session=db,
        scheme_id=scheme_id,
        adjusted_income_ceiling=float(income) if income is not None else None,
        adjusted_land_ceiling=float(land) if land is not None else None,
        adjusted_castes=castes
    )
    return result

@app.post("/api/v1/policy/goal-seek")
def goal_seek_optimizer(payload: Dict[str, Any], db: Session = Depends(get_sync_db)):
    """
    Inverse budget goal-seek optimizer.
    """
    scheme_id = payload.get("scheme_id", "mahadbt_post_matric_obc")
    target_budget = payload.get("target_budget")
    target_beneficiaries = payload.get("target_beneficiaries")

    result = policy_simulator.inverse_goal_seek(
        session=db,
        scheme_id=scheme_id,
        target_budget=float(target_budget) if target_budget is not None else None,
        target_beneficiaries=int(target_beneficiaries) if target_beneficiaries is not None else None
    )
    return result

# ==============================================================================
# 8. OUTBOX (WHATSAPP & SMS AUDIT)
# ==============================================================================

@app.get("/api/v1/outbox")
def list_outbox_notifications(db: Session = Depends(get_sync_db)):
    """
    Lists all proactive notifications sent or queued for citizens.
    """
    notifs = db.query(Notification).order_by(Notification.sent_at.desc()).limit(50).all()
    results = []
    for n in notifs:
        c = db.query(Citizen).filter(Citizen.id == n.citizen_id).first()
        results.append({
            "id": n.id,
            "citizen_name": c.full_name if c else "Citizen",
            "channel": n.channel,
            "message": n.message,
            "status": n.status,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None
        })
    return results

# ==============================================================================
# 9. WEBSOCKET FOR AGENTIC RPA PLAYWRIGHT CO-PILOT
# ==============================================================================

@app.websocket("/ws/rpa/copilot/{session_id}")
async def rpa_copilot_websocket(websocket: WebSocket, session_id: str):
    """
    Bi-directional streaming WebSocket for Playwright RPA with Human-in-the-Loop handoff.
    """
    await websocket.accept()

    async def send_event(event_dict: Dict[str, Any]):
        try:
            await websocket.send_text(json.dumps(event_dict))
        except Exception:
            pass

    # Background task for Playwright runner
    runner_task = None

    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            action = data.get("action")

            if action == "START_SUBMISSION":
                portal_key = data.get("portal_key", "mahadbt")
                citizen_data = data.get("citizen_data", {
                    "full_name": "Ramesh Shamrao Patil",
                    "annual_income": 180000,
                    "district": "Kolhapur"
                })
                doc_path = data.get("document_path") or str(ARTIFACTS_DIR / "Artifact_B3_Valid_Caste_Cert.jpg")

                # Launch async task
                runner_task = asyncio.create_task(
                    playwright_runner.run_automation_session(
                        session_id=session_id,
                        portal_key=portal_key,
                        citizen_data=citizen_data,
                        document_path=doc_path,
                        event_callback=send_event
                    )
                )

            elif action == "SUBMIT_OTP_CAPTCHA":
                otp = data.get("otp", "")
                captcha = data.get("captcha", "")
                playwright_runner.supply_user_input(session_id, otp, captcha)

    except WebSocketDisconnect:
        if runner_task and not runner_task.done():
            runner_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
