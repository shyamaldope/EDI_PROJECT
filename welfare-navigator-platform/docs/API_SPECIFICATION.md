# API Specification: REST & WebSocket Contracts

Base URL: `http://localhost:8000/api/v1`

---

## 1. Citizen & Voice Profile Endpoints

### `POST /citizens`
Register or retrieve citizen profile.
- **Request Body:**
  ```json
  {
    "full_name": "Ramesh Shamrao Patil",
    "phone": "9820012345",
    "ration_card_number": "RC1234567890",
    "dob": "1978-05-15",
    "gender": "MALE",
    "caste_category": "OBC",
    "annual_income": 180000,
    "landholding_acres": 2.5,
    "occupation": "Small Farmer",
    "district": "Kolhapur",
    "state": "Maharashtra",
    "consent_granted": true
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": "c1f7a8...",
    "full_name": "Ramesh Shamrao Patil",
    "phone_hash": "e3b0c44298fc1c149afbf4c8996fb924...",
    "household_id": "8d969eef6ecad3c29a3a629280e686cf...",
    "consent_granted": true,
    "consent_timestamp": "2026-10-22T08:30:00Z"
  }
  ```

### `POST /voice/process`
Processes spoken/text citizen interaction with Bhashini ULCA / fallback.
- **Request:** Multi-part audio file OR JSON text (`{ "text": "माझं नाव रमेश पाटील आहे, उत्पन्न १.८ लाख", "language": "mr" }`).
- **Response (200 OK):**
  ```json
  {
    "extracted_slots": {
      "full_name": "Ramesh Shamrao Patil",
      "annual_income": 180000
    },
    "pii_badge": "[PII SCRUBBED: AADHAAR & PHONE REDACTED]",
    "synthesized_response_audio": "data:audio/mp3;base64,...",
    "response_text": "नमस्कार रमेशजी, आपले उत्पन्न १.८ लाख रुपये नोंदवले गेले आहे.",
    "execution_mode": "[SIMULATED EXTERNAL API]"
  }
  ```

### `DELETE /citizens/{citizen_id}/purge`
Executes DPDP Act 2023 "Right to Erasure" 1-click purge.
- **Response (200 OK):**
  ```json
  {
    "status": "PURGED",
    "citizen_id": "c1f7a8...",
    "files_wiped": 4,
    "records_deleted": ["profile", "documents", "audit_logs", "notifications"],
    "purge_receipt_hash": "a1b2c3d4..."
  }
  ```

---

## 2. Ingestion & Human-in-the-Loop Admin Endpoints

### `POST /admin/ingest-gr`
Uploads a Government Resolution (GR) PDF.
- **Response (200 OK):**
  ```json
  {
    "scheme_id": "s89a...",
    "scheme_name": "Maha Krishi Urja & Samruddhi Yojana 2026",
    "status": "DRAFT_HITL",
    "candidate_ast": {
      "operator": "AND",
      "children": [...]
    },
    "citations": [
      {"field": "annual_income", "page": 2, "clause": "Para 4(a)"}
    ],
    "message": "Scheme ingested as DRAFT_HITL. Admin approval required."
  }
  ```

### `POST /admin/schemes/{scheme_id}/approve`
Admin verifies side-by-side citations and approves the AST.
- **Response (200 OK):**
  ```json
  {
    "scheme_id": "s89a...",
    "status": "ACTIVE",
    "activated_at": "2026-10-22T08:35:00Z",
    "reverse_match_task_id": "rev_task_123",
    "message": "Scheme activated. Reverse-matching triggered across all registered citizens."
  }
  ```

---

## 3. Rule Engine & Scheme Stacker Endpoints

### `GET /citizens/{citizen_id}/schemes`
Evaluates deterministic eligibility, near-misses, and optimal MWIS benefit stack.
- **Response (200 OK):**
  ```json
  {
    "eligible_schemes": [
      {
        "scheme_id": "pm_kisan",
        "scheme_name": "PM-KISAN Samman Nidhi",
        "annual_benefit": 6000,
        "verdict": "ELIGIBLE",
        "audit_signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "condition_results": [
          {"field": "landholding_acres", "operator": "LESS_EQUAL", "limit": 5.0, "actual": 2.5, "passed": true}
        ]
      }
    ],
    "near_miss_schemes": [
      {
        "scheme_id": "scholarship_higher_ed",
        "match_percentage": 92.5,
        "failing_conditions": [
          {
            "field": "income_certificate_validity",
            "reason": "Income certificate expired on 2023-03-31",
            "remediation_action": "Renew Income Certificate at Tehsil Office or Aaple Sarkar Kiosk to unlock ₹50,000 benefit."
          }
        ]
      }
    ],
    "optimal_benefit_stack": {
      "total_annual_benefit": 56000,
      "recommended_schemes": ["pm_kisan", "namo_shetkari", "dr_punjabrao_hostel"],
      "conflicts_resolved": [
        "Excluded Scheme B due to mutual exclusion with Dr. Punjabrao Deshmukh Scheme."
      ]
    }
  }
  ```

---

## 4. Document Auditor & Quality Gate

### `POST /documents/audit`
Performs OCR, RapidFuzz cross-validation, and expiry validation.
- **Request:** Multi-part file + `citizen_id` + `doc_type` (`IDENTITY`, `INCOME`, `CASTE`, `LAND`).
- **Response (200 OK):**
  ```json
  {
    "document_id": "doc_456",
    "blur_score": 142.8,
    "quality_status": "PASS",
    "extracted_fields": {
      "name": "Ramesh S. Patil",
      "annual_income": 180000,
      "valid_until": "2023-03-31"
    },
    "rapidfuzz_name_score": 82.4,
    "name_mismatch_warning": true,
    "affidavit_url": "/api/v1/documents/affidavit/doc_456.pdf",
    "expiry_warning": true,
    "expiry_status": "EXPIRED_ON_2023_03_31"
  }
  ```

### `POST /documents/compress`
Pillow binary-search compressor enforcing the strictly required [20KB, 50KB] bracket.
- **Response (200 OK):**
  ```json
  {
    "original_size_bytes": 1482910,
    "compressed_size_bytes": 38412,
    "status": "SUCCESS_WITHIN_PORTAL_BRACKET",
    "compressed_file_url": "/api/v1/documents/download/doc_456_compressed.jpg"
  }
  ```

---

## 5. Live RPA Co-Pilot & WebSockets

### `WS /ws/rpa/copilot/{session_id}`
Bi-directional streaming WebSocket for Playwright automation.
- **Server Events:**
  - `{"step": "NAVIGATING", "url": "http://localhost:8001/mahadbt"}`
  - `{"step": "FILLING_PERSONAL_DETAILS", "progress": 33}`
  - `{"step": "UPLOADING_DOCUMENT", "file_size_kb": 37.5, "status": "ACCEPTED"}`
  - `{"step": "PAUSED_AWAITING_INPUT", "prompt": "Please enter OTP & CAPTCHA", "screenshot_base64": "..."}`
  - `{"step": "COMPLETED", "tracking_id": "MHA-2026-981245", "receipt_pdf": "..."}`
- **Client Messages:**
  - `{"action": "SUBMIT_OTP_CAPTCHA", "otp": "452109", "captcha": "KR82X"}`

---

## 6. SLA Tracker & Policy Twin Sandbox

### `GET /tracker/applications/{application_id}`
Returns SLA timeline bar, days elapsed vs statutory threshold, and breach status.

### `POST /tracker/grievance/draft`
Generates legal Maharashtra Right to Services (RTS) Act 2015 grievance PDF.

### `POST /policy/simulate`
Forward What-If simulation across all registered citizens with custom parameter levers.

### `POST /policy/goal-seek`
Inverse budget optimizer: computes eligibility thresholds to achieve target budget or beneficiary count.
