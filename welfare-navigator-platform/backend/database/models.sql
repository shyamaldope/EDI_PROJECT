-- Raw DDL Schema for Welfare Navigator Platform (PostgreSQL 16 Compatible)

CREATE TABLE IF NOT EXISTS citizens (
    id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,
    household_id VARCHAR(64) NOT NULL,
    dob VARCHAR(10),
    age INT,
    gender VARCHAR(20),
    caste_category VARCHAR(50),
    annual_income DOUBLE PRECISION,
    landholding_acres DOUBLE PRECISION DEFAULT 0.0,
    occupation VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100) DEFAULT 'Maharashtra',
    has_disability BOOLEAN DEFAULT FALSE,
    is_student BOOLEAN DEFAULT FALSE,
    education_level VARCHAR(100),
    consent_granted BOOLEAN DEFAULT FALSE NOT NULL,
    consent_timestamp VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_citizens_phone_hash ON citizens(phone_hash);
CREATE INDEX IF NOT EXISTS idx_citizens_household_id ON citizens(household_id);

CREATE TABLE IF NOT EXISTS citizen_documents (
    id VARCHAR(36) PRIMARY KEY,
    citizen_id VARCHAR(36) NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    compressed_path VARCHAR(500),
    ocr_data JSONB,
    blur_score DOUBLE PRECISION,
    quality_status VARCHAR(20) DEFAULT 'PENDING',
    validation_status VARCHAR(50) DEFAULT 'PENDING',
    validation_errors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_citizen_id ON citizen_documents(citizen_id);

CREATE TABLE IF NOT EXISTS schemes (
    id VARCHAR(100) PRIMARY KEY,
    scheme_code VARCHAR(100) UNIQUE NOT NULL,
    scheme_name VARCHAR(255) NOT NULL,
    scheme_name_mr VARCHAR(255),
    department VARCHAR(255) NOT NULL,
    target_beneficiary VARCHAR(255) NOT NULL,
    benefit_amount DOUBLE PRECISION NOT NULL,
    benefit_type VARCHAR(100) NOT NULL,
    sla_days INT DEFAULT 30,
    ast_rule JSONB NOT NULL,
    citations JSONB,
    mutual_exclusions JSONB,
    dom_mapping_key VARCHAR(100),
    status VARCHAR(50) DEFAULT 'DRAFT_HITL',
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schemes_status ON schemes(status);
CREATE INDEX IF NOT EXISTS idx_schemes_ast_rule_gin ON schemes USING gin (ast_rule);

CREATE TABLE IF NOT EXISTS scheme_version_diffs (
    id VARCHAR(36) PRIMARY KEY,
    scheme_id VARCHAR(100) NOT NULL,
    old_version INT NOT NULL,
    new_version INT NOT NULL,
    ast_diff JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id VARCHAR(36) PRIMARY KEY,
    citizen_id VARCHAR(36) NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
    scheme_id VARCHAR(100) NOT NULL REFERENCES schemes(id),
    application_status VARCHAR(50) DEFAULT 'SUBMITTED',
    portal_tracking_id VARCHAR(100),
    submission_receipt_path VARCHAR(500),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sla_deadline TIMESTAMP,
    days_elapsed INT DEFAULT 0,
    grievance_filed BOOLEAN DEFAULT FALSE,
    audit_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_applications_citizen ON applications(citizen_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(application_status);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    citizen_id VARCHAR(36) NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
    scheme_id VARCHAR(100) NOT NULL REFERENCES schemes(id),
    action VARCHAR(100) NOT NULL,
    input_snapshot JSONB,
    rule_evaluated JSONB,
    verdict VARCHAR(50) NOT NULL,
    decision_signature VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_signature ON audit_logs(decision_signature);

CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    citizen_id VARCHAR(36) NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
    channel VARCHAR(50) DEFAULT 'WHATSAPP',
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'SIMULATED',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
