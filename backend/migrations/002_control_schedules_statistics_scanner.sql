CREATE SCHEMA IF NOT EXISTS education_control;

CREATE TABLE IF NOT EXISTS education_control.exam_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID REFERENCES school.academic_years(id),
    grade_id UUID REFERENCES school.grades(id),
    subject_id UUID REFERENCES education_control.subjects(id),
    exam_term_id UUID REFERENCES education_control.exam_terms(id),
    exam_round_id UUID REFERENCES education_control.exam_rounds(id),
    exam_date DATE NOT NULL,
    starts_at TIME,
    ends_at TIME,
    duration_minutes INT,
    committee_notes TEXT,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.committee_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    committee_id UUID NOT NULL REFERENCES education_control.committees(id),
    student_id UUID NOT NULL REFERENCES school.students(id),
    seat_number_id UUID REFERENCES education_control.seat_numbers(id),
    row_no INT,
    seat_position TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(committee_id, student_id)
);

CREATE TABLE IF NOT EXISTS education_control.control_statistics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_name TEXT NOT NULL,
    academic_year_id UUID REFERENCES school.academic_years(id),
    exam_term_id UUID REFERENCES education_control.exam_terms(id),
    exam_round_id UUID REFERENCES education_control.exam_rounds(id),
    total_institutes INT NOT NULL DEFAULT 0,
    total_students INT NOT NULL DEFAULT 0,
    total_subjects INT NOT NULL DEFAULT 0,
    total_committees INT NOT NULL DEFAULT 0,
    total_scores INT NOT NULL DEFAULT 0,
    passed_students INT NOT NULL DEFAULT 0,
    failed_students INT NOT NULL DEFAULT 0,
    pending_students INT NOT NULL DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control.scanner_import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name TEXT NOT NULL,
    scanner_type TEXT NOT NULL DEFAULT 'barcode',
    source_context TEXT,
    total_scans INT NOT NULL DEFAULT 0,
    accepted_scans INT NOT NULL DEFAULT 0,
    rejected_scans INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS education_control.scanner_import_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES education_control.scanner_import_batches(id) ON DELETE CASCADE,
    raw_code TEXT NOT NULL,
    normalized_code TEXT NOT NULL,
    scan_type TEXT NOT NULL DEFAULT 'student',
    matched_student_id UUID REFERENCES school.students(id),
    matched_seat_number_id UUID REFERENCES education_control.seat_numbers(id),
    matched_committee_id UUID REFERENCES education_control.committees(id),
    result_status TEXT NOT NULL DEFAULT 'pending',
    result_message TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_exam_schedules_date ON education_control.exam_schedules(exam_date);
CREATE INDEX IF NOT EXISTS ix_scanner_events_code ON education_control.scanner_import_events(normalized_code);
CREATE INDEX IF NOT EXISTS ix_scanner_events_batch ON education_control.scanner_import_events(batch_id);
CREATE INDEX IF NOT EXISTS ix_committee_assignments_committee ON education_control.committee_assignments(committee_id);
CREATE INDEX IF NOT EXISTS ix_committee_assignments_student ON education_control.committee_assignments(student_id);
