CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS hr;
CREATE SCHEMA IF NOT EXISTS timetable;
CREATE SCHEMA IF NOT EXISTS operations;

CREATE TABLE IF NOT EXISTS core.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE,
    name_ar TEXT NOT NULL,
    organization_type TEXT NOT NULL DEFAULT 'school_group',
    parent_id UUID REFERENCES core.organizations(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.app_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    scope_name TEXT NOT NULL,
    route_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    sort_order INT NOT NULL DEFAULT 0,
    feature_flag TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES core.app_modules(id),
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    action_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES core.organizations(id),
    username TEXT NOT NULL UNIQUE,
    display_name_ar TEXT NOT NULL,
    email TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_scope TEXT NOT NULL,
    owner_id UUID,
    document_type TEXT NOT NULL,
    title_ar TEXT NOT NULL,
    file_path TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.migration_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_code TEXT NOT NULL UNIQUE,
    module_code TEXT NOT NULL,
    description_ar TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES core.organizations(id),
    code TEXT UNIQUE,
    name_ar TEXT NOT NULL,
    manager_employee_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE,
    name_ar TEXT NOT NULL,
    job_family TEXT,
    is_teaching_job BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES core.organizations(id),
    department_id UUID REFERENCES hr.departments(id),
    job_id UUID REFERENCES hr.jobs(id),
    employee_no TEXT UNIQUE,
    national_id TEXT,
    full_name_ar TEXT NOT NULL,
    employment_type TEXT,
    hire_date DATE,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.teacher_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL UNIQUE REFERENCES hr.employees(id) ON DELETE CASCADE,
    specialization TEXT,
    weekly_load_target INT NOT NULL DEFAULT 0,
    can_invigilate BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES hr.employees(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    status TEXT NOT NULL DEFAULT 'present',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(employee_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS hr.leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES hr.employees(id) ON DELETE CASCADE,
    leave_type TEXT NOT NULL,
    starts_on DATE NOT NULL,
    ends_on DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    approved_by UUID REFERENCES hr.employees(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hr.payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES core.organizations(id),
    payroll_month DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    gross_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    net_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.guardians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    national_id TEXT,
    full_name_ar TEXT NOT NULL,
    phone TEXT,
    relation_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.student_guardians (
    student_id UUID NOT NULL REFERENCES school.students(id) ON DELETE CASCADE,
    guardian_id UUID NOT NULL REFERENCES school.guardians(id) ON DELETE CASCADE,
    relation_type TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (student_id, guardian_id)
);

CREATE TABLE IF NOT EXISTS school.classrooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institute_id UUID REFERENCES school.institutes(id),
    grade_id UUID REFERENCES school.grades(id),
    code TEXT,
    name_ar TEXT NOT NULL,
    capacity INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institute_id UUID REFERENCES school.institutes(id),
    code TEXT,
    name_ar TEXT NOT NULL,
    room_type TEXT NOT NULL DEFAULT 'classroom',
    capacity INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS timetable.school_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS timetable.periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institute_id UUID REFERENCES school.institutes(id),
    period_no INT NOT NULL,
    name_ar TEXT NOT NULL,
    starts_at TIME NOT NULL,
    ends_at TIME NOT NULL,
    is_break BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(institute_id, period_no)
);

CREATE TABLE IF NOT EXISTS timetable.lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID REFERENCES school.academic_years(id),
    classroom_id UUID REFERENCES school.classrooms(id),
    subject_id UUID REFERENCES education_control.subjects(id),
    teacher_id UUID REFERENCES hr.teacher_profiles(id),
    room_id UUID REFERENCES school.rooms(id),
    school_day_id UUID REFERENCES timetable.school_days(id),
    period_id UUID REFERENCES timetable.periods(id),
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS timetable.conflict_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES timetable.lessons(id) ON DELETE CASCADE,
    conflict_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning',
    message_ar TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS operations.import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_code TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    rows_total INT NOT NULL DEFAULT 0,
    rows_success INT NOT NULL DEFAULT 0,
    rows_failed INT NOT NULL DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS operations.report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_code TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    output_type TEXT NOT NULL DEFAULT 'pdf',
    template_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS operations.feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO core.app_modules(code, name_ar, scope_name, route_path, status, sort_order, feature_flag)
VALUES
('core', 'النواة المشتركة', 'Core Platform', '/platform', 'ready', 10, 'core_platform'),
('hr', 'برنامج الموظفين', 'HR / Employee Program', '/hr', 'schema_ready', 20, 'hr_program'),
('school', 'برنامج المدارس', 'School Program', '/school', 'schema_ready', 30, 'school_program'),
('timetable', 'الجدول المدرسي', 'School Timetable', '/timetable', 'schema_ready', 40, 'school_timetable'),
('education-control', 'برنامج الكنترول', 'Education Control', '/education-control', 'started', 50, 'education_control'),
('access-mirror', 'مرآة Access', 'Access Mirror', '/access-mirror', 'started', 60, 'access_mirror'),
('operations', 'التشغيل والتقارير', 'Operations', '/operations', 'schema_ready', 70, 'operations')
ON CONFLICT (code) DO UPDATE SET
    name_ar = EXCLUDED.name_ar,
    scope_name = EXCLUDED.scope_name,
    route_path = EXCLUDED.route_path,
    status = EXCLUDED.status,
    sort_order = EXCLUDED.sort_order,
    feature_flag = EXCLUDED.feature_flag;

INSERT INTO operations.feature_flags(code, name_ar, is_enabled)
VALUES
('core_platform', 'تشغيل النواة المشتركة', TRUE),
('hr_program', 'تشغيل برنامج الموظفين', TRUE),
('school_program', 'تشغيل برنامج المدارس', TRUE),
('school_timetable', 'تشغيل الجدول المدرسي', TRUE),
('education_control', 'تشغيل برنامج الكنترول', TRUE),
('access_mirror', 'تشغيل مرآة Access', TRUE),
('operations', 'تشغيل العمليات والتقارير', TRUE)
ON CONFLICT (code) DO UPDATE SET name_ar = EXCLUDED.name_ar, is_enabled = EXCLUDED.is_enabled;

INSERT INTO core.migration_registry(migration_code, module_code, description_ar)
VALUES
('003_unified_erp_platform', 'core', 'تثبيت Core + HR + School extensions + Timetable + Operations حسب الوثيقة النهائية')
ON CONFLICT (migration_code) DO NOTHING;

INSERT INTO timetable.school_days(code, name_ar, sort_order)
VALUES
('sat', 'السبت', 1),
('sun', 'الأحد', 2),
('mon', 'الاثنين', 3),
('tue', 'الثلاثاء', 4),
('wed', 'الأربعاء', 5),
('thu', 'الخميس', 6)
ON CONFLICT (code) DO NOTHING;
