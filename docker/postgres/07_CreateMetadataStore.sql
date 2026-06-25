-- ============================================================
-- SCHEMA SETUP
-- ============================================================

-- CREATE SCHEMA IF NOT EXISTS ib_metadata;
SET search_path TO ib_metadata;

-- ============================================================
-- CLEAN UP
-- ============================================================
-- DROP TABLE IF EXISTS sensitivity_levels CASCADE;
-- DROP TABLE IF EXISTS pii_categories CASCADE;
-- DROP TABLE IF EXISTS roles CASCADE;
-- DROP TABLE IF EXISTS masking_functions CASCADE;
-- DROP TABLE IF EXISTS tables_metadata CASCADE;
-- DROP TABLE IF EXISTS columns_metadata CASCADE;
-- DROP TABLE IF EXISTS access_policies;
-- DROP INDEX IF EXISTS idx_columns_table_id;
-- DROP INDEX IF EXISTS idx_columns_pii_category;
-- DROP INDEX IF EXISTS idx_columns_sensitivity;
-- DROP INDEX IF EXISTS idx_access_policy_role;
-- DROP INDEX IF EXISTS idx_access_policy_sensitivity;
-- DROP TYPE IF EXISTS detection_method_enum;
-- DROP TYPE IF EXISTS policy_action_enum;

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE detection_method_enum AS ENUM (
    'REGEX',
    'LLM',
    'HYBRID',
    'MANUAL',
    'UNKNOWN'
);

CREATE TYPE policy_action_enum AS ENUM (
    'ALLOW',
    'MASK',
    'DENY'
);

-- ============================================================
-- METADATA STORE SCHEMA
-- ============================================================

CREATE TABLE sensitivity_levels (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE pii_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    regex_pattern TEXT,
    default_sensitivity_level_id INTEGER REFERENCES sensitivity_levels(id)
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE masking_functions (
    id SERIAL PRIMARY KEY,
    function_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE tables_metadata (
    id SERIAL PRIMARY KEY,
    namespace VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- constraints
    UNIQUE(namespace, table_name)
);

CREATE TABLE columns_metadata (
    id SERIAL PRIMARY KEY,
    table_id INTEGER NOT NULL
        REFERENCES tables_metadata(id)
        ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    pii_category_id INTEGER
        REFERENCES pii_categories(id),
    sensitivity_level_id INTEGER
        REFERENCES sensitivity_levels(id),
    detection_method detection_method_enum,
    confidence_score NUMERIC(5,4),
    sample_values JSONB,
    scanned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- constraints
    UNIQUE(table_id, column_name)
);

-- ACCESS CONTROL

CREATE TABLE access_policies (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL
        REFERENCES roles(id)
        ON DELETE CASCADE,
    sensitivity_level_id INTEGER NOT NULL
        REFERENCES sensitivity_levels(id),
    action policy_action_enum NOT NULL,
    masking_function_id INTEGER
        REFERENCES masking_functions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- constraints
    UNIQUE(role_id, sensitivity_level_id)
);

-- INDEXES

CREATE INDEX idx_columns_table_id
ON columns_metadata(table_id);

CREATE INDEX idx_columns_pii_category
ON columns_metadata(pii_category_id);

CREATE INDEX idx_columns_sensitivity
ON columns_metadata(sensitivity_level_id);

CREATE INDEX idx_access_policy_role
ON access_policies(role_id);

CREATE INDEX idx_access_policy_sensitivity
ON access_policies(sensitivity_level_id);

-- SEED DATA

INSERT INTO sensitivity_levels
(code, description)
VALUES
('HIGH', 'Critical sensitive information'),
('MEDIUM', 'Moderately sensitive information'),
('LOW', 'Low sensitivity information'),
('NONE', 'Non-sensitive information');

INSERT INTO roles
(role_name, description)
VALUES
('ADMIN', 'Full access'),
('ANALYST', 'Business analyst'),
('AUDITOR', 'Compliance auditor');

INSERT INTO masking_functions
(function_name, description)
VALUES
('PARTIAL_MASK', 'Mask a portion of the value'),
('HASH_MASK', 'SHA256 hash masking'),
('REDACT', 'Replace with [REDACTED]'),
('NULLIFY', 'Replace with NULL');

INSERT INTO pii_categories
(
    code,
    description,
    regex_pattern,
    default_sensitivity_level_id
)
VALUES
(
    'NATIONAL_ID',
    'Vietnamese citizen identification number',
    '^[0-9]{12}$',
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),
(
    'PHONE',
    'Vietnamese mobile phone number',
    '^(03|05|07|08|09)[0-9]{8}$',
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),
(
    'EMAIL',
    'Personal email address',
    '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),
(
    'ADDRESS',
    'Residential address',
    NULL,
    (SELECT id FROM sensitivity_levels WHERE code='LOW')
),
(
    'FULL_NAME',
    'Personal full name',
    NULL,
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),
(
    'BANK_ACCOUNT',
    'Bank account number',
    '^[0-9]{8,20}$',
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),
(
    'TAX_CODE',
    'Vietnamese tax identification number',
    '^[0-9]{10}(-[0-9]{3})?$',
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
);