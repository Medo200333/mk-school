CREATE SCHEMA IF NOT EXISTS school;
CREATE SCHEMA IF NOT EXISTS education_control;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS school.institutes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE,
    name_ar TEXT NOT NULL,
    institute_type TEXT,
    education_stage TEXT,
    zone_name TEXT,
    administration_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    starts_on DATE,
    ends_on DATE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stage_code TEXT NOT NULL,
    grade_code TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(stage_code, grade_code)
);

CREATE TABLE IF NOT EXISTS school.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legacy_access_id TEXT,
    national_id TEXT,
    student_name_ar TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    religion TEXT,
    health_status TEXT,
    institute_id UUID REFERENCES school.institutes(id),
    grade_id UUID REFERENCES school.grades(id),
    class_name TEXT,
    enrollment_status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.exam_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID REFERENCES school.academic_years(id),
    code TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(academic_year_id, code)
);

CREATE TABLE IF NOT EXISTS education_control.exam_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID REFERENCES school.academic_years(id),
    code TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(academic_year_id, code)
);

CREATE TABLE IF NOT EXISTS education_control.subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade_id UUID REFERENCES school.grades(id),
    code TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    max_score NUMERIC(8,2),
    min_score NUMERIC(8,2),
    has_written BOOLEAN NOT NULL DEFAULT TRUE,
    has_coursework BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(grade_id, code)
);

CREATE TABLE IF NOT EXISTS education_control.committees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institute_id UUID REFERENCES school.institutes(id),
    academic_year_id UUID REFERENCES school.academic_years(id),
    committee_no TEXT NOT NULL,
    name_ar TEXT,
    capacity INT NOT NULL DEFAULT 0,
    location TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.seat_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES school.students(id),
    academic_year_id UUID REFERENCES school.academic_years(id),
    committee_id UUID REFERENCES education_control.committees(id),
    seat_no TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(academic_year_id, seat_no),
    UNIQUE(academic_year_id, student_id)
);

CREATE TABLE IF NOT EXISTS education_control.score_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES school.students(id),
    subject_id UUID NOT NULL REFERENCES education_control.subjects(id),
    exam_term_id UUID REFERENCES education_control.exam_terms(id),
    exam_round_id UUID REFERENCES education_control.exam_rounds(id),
    written_score NUMERIC(8,2),
    coursework_score NUMERIC(8,2),
    total_score NUMERIC(8,2) GENERATED ALWAYS AS (
        COALESCE(written_score, 0) + COALESCE(coursework_score, 0)
    ) STORED,
    is_absent BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(student_id, subject_id, exam_term_id, exam_round_id)
);

CREATE TABLE IF NOT EXISTS education_control.results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES school.students(id),
    academic_year_id UUID REFERENCES school.academic_years(id),
    total_score NUMERIC(10,2) NOT NULL DEFAULT 0,
    percentage NUMERIC(6,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    rank_no INT,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(student_id, academic_year_id)
);

CREATE TABLE IF NOT EXISTS education_control.activation_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file TEXT NOT NULL,
    activation_code TEXT NOT NULL,
    activation_name_ar TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.access_import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file TEXT NOT NULL,
    source_database TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    tables_count INT NOT NULL DEFAULT 0,
    rows_count INT NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.access_import_table_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES education_control.access_import_batches(id),
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    rows_count INT NOT NULL DEFAULT 0,
    columns_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    sample_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    classification TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO school.academic_years(name, starts_on, ends_on, is_current)
VALUES ('2025-2026', '2025-09-01', '2026-08-31', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO education_control.activation_settings(source_file, activation_code, activation_name_ar)
VALUES
('تفعيل الفصل الدراسى الأول 2025-2026.accdb', '111', 'تفعيل الفصل الدراسي الأول'),
('تفعيل الفصل الدراسى الثانى 2025-2026.accdb', '222', 'تفعيل الفصل الدراسي الثاني'),
('تفعيل الدور الثانى 2025-2026.accdb', '333', 'تفعيل الدور الثاني')
ON CONFLICT DO NOTHING;
