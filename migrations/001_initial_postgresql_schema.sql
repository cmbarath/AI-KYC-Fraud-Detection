CREATE TABLE IF NOT EXISTS kyc_applications (
    id VARCHAR(36) PRIMARY KEY,
    application_number VARCHAR(32) NOT NULL UNIQUE,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    date_of_birth VARCHAR(10) NOT NULL,
    email VARCHAR(128) NOT NULL,
    phone_number VARCHAR(32) NOT NULL,
    id_type VARCHAR(32) NOT NULL,
    id_number VARCHAR(64) NOT NULL,
    id_hash VARCHAR(64) NOT NULL,
    address_line VARCHAR(256) NOT NULL,
    city VARCHAR(64) NOT NULL,
    state VARCHAR(64) NOT NULL,
    country VARCHAR(64) NOT NULL DEFAULT 'Simulatedland',
    declared_income VARCHAR(32),
    employment_type VARCHAR(64) DEFAULT 'Salaried',
    status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED',
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_kyc_applications_application_number
    ON kyc_applications (application_number);
CREATE INDEX IF NOT EXISTS ix_kyc_applications_email
    ON kyc_applications (email);
CREATE INDEX IF NOT EXISTS ix_kyc_applications_phone_number
    ON kyc_applications (phone_number);
CREATE INDEX IF NOT EXISTS ix_kyc_applications_id_number
    ON kyc_applications (id_number);
CREATE INDEX IF NOT EXISTS ix_kyc_applications_id_hash
    ON kyc_applications (id_hash);
CREATE INDEX IF NOT EXISTS ix_kyc_applications_status
    ON kyc_applications (status);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL
        REFERENCES kyc_applications(id) ON DELETE CASCADE,
    document_type VARCHAR(32) NOT NULL,
    file_name VARCHAR(256) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    extracted_text TEXT,
    extracted_name VARCHAR(128),
    extracted_id_number VARCHAR(64),
    extracted_dob VARCHAR(32),
    name_match_score DOUBLE PRECISION DEFAULT 0.0,
    id_match_score DOUBLE PRECISION DEFAULT 0.0,
    dob_match_score DOUBLE PRECISION DEFAULT 0.0,
    overall_match_score DOUBLE PRECISION DEFAULT 0.0,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_documents_applicant_id
    ON documents (applicant_id);
CREATE INDEX IF NOT EXISTS ix_documents_file_hash
    ON documents (file_hash);

CREATE TABLE IF NOT EXISTS fraud_evaluations (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL
        REFERENCES kyc_applications(id) ON DELETE CASCADE,
    fraud_probability DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_tier VARCHAR(16) NOT NULL,
    model_name VARCHAR(64) DEFAULT 'XGBoost_Classifier',
    model_version VARCHAR(32) DEFAULT 'v1.0',
    top_risk_factors TEXT,
    shap_summary TEXT,
    automated_decision VARCHAR(32) DEFAULT 'MANUAL_REVIEW',
    evaluated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_fraud_evaluations_applicant_id
    ON fraud_evaluations (applicant_id);

CREATE TABLE IF NOT EXISTS transaction_records (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL
        REFERENCES kyc_applications(id) ON DELETE CASCADE,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(8) DEFAULT 'USD',
    transaction_type VARCHAR(32) DEFAULT 'TRANSFER',
    merchant_category VARCHAR(64) DEFAULT 'General',
    ip_address VARCHAR(45),
    device_id VARCHAR(64),
    location_city VARCHAR(64),
    is_anomalous BOOLEAN DEFAULT FALSE,
    anomaly_score DOUBLE PRECISION DEFAULT 0.0,
    anomaly_reasons TEXT,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_transaction_records_applicant_id
    ON transaction_records (applicant_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36)
        REFERENCES kyc_applications(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64) DEFAULT 'SYSTEM',
    description TEXT NOT NULL,
    metadata_json TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_applicant_id
    ON audit_logs (applicant_id);
