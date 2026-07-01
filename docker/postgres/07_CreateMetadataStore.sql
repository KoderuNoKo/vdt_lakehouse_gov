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
    column_name_aliases TEXT[],
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
    -- column's raw metadata
    id SERIAL PRIMARY KEY,
    table_id INTEGER NOT NULL
        REFERENCES tables_metadata(id)
        ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    sample_values JSONB,

    -- latest/active pii scan record
    pii_category_id INTEGER
        REFERENCES pii_categories(id),
    sensitivity_level_id INTEGER    -- can override default sensitivity, as stated by project specs
        REFERENCES sensitivity_levels(id),
    detection_method detection_method_enum,
    confidence_score NUMERIC(5,4),
    
    -- quick filter
    scanned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- constraints
    UNIQUE(table_id, column_name)
);

-- historical log of pii scans
CREATE TABLE pii_scan_record (
    id SERIAL PRIMARY KEY,
    column_id INT REFERENCES columns_metadata(id),
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_method detection_method_enum,
    confidence_score NUMERIC(5,4),
    detected_category_id INT REFERENCES pii_categories(id)
    -- raw_output JSONB -- useful for LLM debugging/audit (not yet used)
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
    column_name_aliases,
    default_sensitivity_level_id
)
VALUES

(
    'NATIONAL_ID',
    'Vietnamese citizen identification number',
    '[0-9]{12}',
    ARRAY[
        'cccd',
        'cmnd',
        'citizenid',
        'nationalid',
        'identitynumber',
        'personalid'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),

(
    'BANK_ACCOUNT',
    'Bank account number',
    '[0-9]{8,20}',
    ARRAY[
        'bankaccount',
        'accountnumber',
        'bankacc',
        'stk',
        'sotaikhoan'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),

(
    'TAX_CODE',
    'Vietnamese tax identification number',
    '[0-9]{10}(-[0-9]{3})?',
    ARRAY[
        'taxcode',
        'taxid',
        'mst',
        'masothue'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),

(
    'SALARY',
    'Salary or wage information',
    NULL,
    ARRAY[
        'salary',
        'wage',
        'income',
        'monthlysalary',
        'annualsalary',
        'luong',
        'mucluong'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='HIGH')
),

(
    'PHONE',
    'Vietnamese mobile phone number',
    '(03|05|07|08|09)[0-9]{8}',
    ARRAY[
        'phone',
        'phonenumber',
        'mobile',
        'mobilephone',
        'telephone',
        'tel',
        'contactnumber',
        'sdt',
        'sodienthoai'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),

(
    'EMAIL',
    'Personal email address',
    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    ARRAY[
        'email',
        'emailaddress',
        'mail'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),

(
    'FULL_NAME',
    'Personal full name',
    NULL,
    ARRAY[
        'fullname',
        'name',
        'customername',
        'employeename',
        'citizenname',
        'personname',
        'hoten',
        'hovaten'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='MEDIUM')
),

(
    'ADDRESS',
    'Residential address',
    NULL,
    ARRAY[
        'address',
        'homeaddress',
        'residentialaddress',
        'location',
        'diachi'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='LOW')
),

(
    'DATE_OF_BIRTH',
    'Date of birth',
    NULL,
    ARRAY[
        'dob',
        'birthdate',
        'birthday',
        'dateofbirth',
        'ngaysinh'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='LOW')
),

(
    'WORKPLACE',
    'Workplace or employer',
    NULL,
    ARRAY[
        'workplace',
        'company',
        'companyname',
        'organization',
        'organizationname',
        'employer',
        'office',
        'worklocation'
    ],
    (SELECT id FROM sensitivity_levels WHERE code='LOW')
);

INSERT INTO access_policies (role_id, sensitivity_level_id, action, masking_function_id)
VALUES
    -- ROLE: ADMIN. Full access to all data.
    ((SELECT id FROM roles WHERE role_name = 'ADMIN'), (SELECT id FROM sensitivity_levels WHERE code = 'HIGH'), 'ALLOW', NULL),
    ((SELECT id FROM roles WHERE role_name = 'ADMIN'), (SELECT id FROM sensitivity_levels WHERE code = 'MEDIUM'), 'ALLOW', NULL),
    ((SELECT id FROM roles WHERE role_name = 'ADMIN'), (SELECT id FROM sensitivity_levels WHERE code = 'LOW'), 'ALLOW', NULL),
    ((SELECT id FROM roles WHERE role_name = 'ADMIN'), (SELECT id FROM sensitivity_levels WHERE code = 'NONE'), 'ALLOW', NULL),

    -- ROLE: ANALYST. Can see non-sensitive data, but sensitive data is dynamically masked to preserve analytical utility.
    -- HIGH (e.g., CCCD, Bank Account): Hash masking to allow JOINs and aggregations without exposing raw PII.
    ((SELECT id FROM roles WHERE role_name = 'ANALYST'), (SELECT id FROM sensitivity_levels WHERE code = 'HIGH'), 'MASK', (SELECT id FROM masking_functions WHERE function_name = 'HASH_MASK')),
    -- MEDIUM (e.g., Phone, Email, Name): Partial masking (e.g., ***@email.com, 098****321).
    ((SELECT id FROM roles WHERE role_name = 'ANALYST'), (SELECT id FROM sensitivity_levels WHERE code = 'MEDIUM'), 'MASK', (SELECT id FROM masking_functions WHERE function_name = 'PARTIAL_MASK')),
    -- LOW / NONE: Full access (e.g., general addresses, dates).
    ((SELECT id FROM roles WHERE role_name = 'ANALYST'), (SELECT id FROM sensitivity_levels WHERE code = 'LOW'), 'ALLOW', NULL),
    ((SELECT id FROM roles WHERE role_name = 'ANALYST'), (SELECT id FROM sensitivity_levels WHERE code = 'NONE'), 'ALLOW', NULL),

    -- ROLE: AUDITOR. Strict compliance. Redacts any PII.
    -- HIGH & MEDIUM: Completely redacted ([REDACTED]).
    ((SELECT id FROM roles WHERE role_name = 'AUDITOR'), (SELECT id FROM sensitivity_levels WHERE code = 'HIGH'), 'MASK', (SELECT id FROM masking_functions WHERE function_name = 'REDACT')),
    ((SELECT id FROM roles WHERE role_name = 'AUDITOR'), (SELECT id FROM sensitivity_levels WHERE code = 'MEDIUM'), 'MASK', (SELECT id FROM masking_functions WHERE function_name = 'REDACT')),
    
    -- LOW / NONE: Full access to review non-sensitive operational data.
    ((SELECT id FROM roles WHERE role_name = 'AUDITOR'), (SELECT id FROM sensitivity_levels WHERE code = 'LOW'), 'ALLOW', NULL),
    ((SELECT id FROM roles WHERE role_name = 'AUDITOR'), (SELECT id FROM sensitivity_levels WHERE code = 'NONE'), 'ALLOW', NULL);