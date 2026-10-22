import os
import random
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mock Government Portals", description="Self-hosted clones of MahaDBT and PM-KISAN for ethical RPA testing")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTAL_DIR = Path(__file__).resolve().parent

# Active OTP store for verification simulation
otp_store = {}

@app.get("/mahadbt", response_class=HTMLResponse)
async def get_mahadbt():
    html_file = PORTAL_DIR / "mahadbt_clone" / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/pmkisan", response_class=HTMLResponse)
async def get_pmkisan():
    html_file = PORTAL_DIR / "pmkisan_clone" / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/mahadbt/upload")
async def upload_mahadbt_doc(file: UploadFile = File(...)):
    """
    Enforces strict government portal file size constraint: 20KB to 50KB.
    """
    content = await file.read()
    size_bytes = len(content)
    size_kb = round(size_bytes / 1024.0, 2)

    if size_bytes < 20 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"MahaDBT Validation Error: File size ({size_kb} KB) is below minimum threshold of 20 KB. Upload rejected."
        )
    if size_bytes > 50 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"MahaDBT Validation Error: File size ({size_kb} KB) exceeds maximum limit of 50 KB. Upload rejected."
        )

    return {
        "status": "ACCEPTED",
        "filename": file.filename,
        "size_bytes": size_bytes,
        "size_kb": size_kb,
        "message": "Document verified and stored successfully within [20KB, 50KB] bracket."
    }

@app.get("/api/mahadbt/challenge")
async def get_challenge():
    """Generates CAPTCHA text and 6-digit OTP for HITL handoff"""
    captcha_text = f"MHA{random.randint(100, 999)}"
    otp = f"{random.randint(100000, 999999)}"
    session_id = str(uuid.uuid4())[:8]
    otp_store[session_id] = {"captcha": captcha_text, "otp": otp}
    return {
        "session_id": session_id,
        "captcha": captcha_text,
        "otp_hint": otp, # Shown on mock portal for easy citizen verification
        "message": "Enter the CAPTCHA and OTP in the form."
    }

@app.post("/api/mahadbt/submit")
async def submit_mahadbt(
    full_name: str = Form(...),
    session_id: str = Form("default"),
    captcha: str = Form(...),
    otp: str = Form(...)
):
    """Final submission endpoint after OTP verification"""
    tracking_id = f"MHA-2026-{random.randint(100000, 999999)}"
    return {
        "status": "SUCCESS",
        "portal": "MahaDBT Post-Matric Scholarship Portal",
        "tracking_id": tracking_id,
        "citizen_name": full_name,
        "submission_date": "2026-10-22T09:00:00Z",
        "receipt_url": f"/api/mahadbt/receipt/{tracking_id}",
        "message": f"Application submitted successfully. Your Application ID is {tracking_id}."
    }

@app.post("/api/pmkisan/upload")
async def upload_pmkisan_doc(file: UploadFile = File(...)):
    content = await file.read()
    size_bytes = len(content)
    size_kb = round(size_bytes / 1024.0, 2)
    if size_bytes < 20 * 1024 or size_bytes > 50 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"PM-KISAN Validation Error: Document size ({size_kb} KB) must be between 20 KB and 50 KB."
        )
    return {"status": "ACCEPTED", "size_kb": size_kb}

@app.post("/api/pmkisan/submit")
async def submit_pmkisan(farmer_name: str = Form(...), captcha: str = Form(...), otp: str = Form(...)):
    tracking_id = f"PMK-2026-{random.randint(100000, 999999)}"
    return {
        "status": "SUCCESS",
        "portal": "PM-KISAN Samman Nidhi Portal",
        "tracking_id": tracking_id,
        "farmer_name": farmer_name,
        "submission_date": "2026-10-22T09:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
