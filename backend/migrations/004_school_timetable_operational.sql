CREATE SCHEMA IF NOT EXISTS school;

CREATE TABLE IF NOT EXISTS school.teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES hr.employees(id),
    teacher_code TEXT UNIQUE,
    teacher_name_ar TEXT NOT NULL,
    phone TEXT,
    specialization TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE school.teachers ADD COLUMN IF NOT EXISTS employee_id UUID REFERENCES hr.employees(id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_school_teachers_employee_id
ON school.teachers(employee_id)
WHERE employee_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS school.classrooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_code TEXT UNIQUE,
    room_name_ar TEXT NOT NULL,
    name_ar TEXT,
    capacity INT NOT NULL DEFAULT 0,
    floor_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE school.classrooms ADD COLUMN IF NOT EXISTS room_code TEXT;
ALTER TABLE school.classrooms ADD COLUMN IF NOT EXISTS room_name_ar TEXT;
ALTER TABLE school.classrooms ADD COLUMN IF NOT EXISTS name_ar TEXT;
ALTER TABLE school.classrooms ADD COLUMN IF NOT EXISTS floor_name TEXT;
UPDATE school.classrooms
SET room_name_ar = COALESCE(room_name_ar, name_ar, code, 'قاعة بدون اسم')
WHERE room_name_ar IS NULL;
UPDATE school.classrooms
SET name_ar = COALESCE(name_ar, room_name_ar)
WHERE name_ar IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_school_classrooms_room_code
ON school.classrooms(room_code)
WHERE room_code IS NOT NULL;

CREATE TABLE IF NOT EXISTS school.school_classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_code TEXT UNIQUE NOT NULL,
    class_name_ar TEXT NOT NULL,
    stage_name_ar TEXT,
    grade_name_ar TEXT,
    capacity INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_code TEXT UNIQUE,
    subject_name_ar TEXT NOT NULL,
    color_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.curriculum_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_class_id UUID NOT NULL REFERENCES school.school_classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES school.subjects(id),
    teacher_id UUID REFERENCES school.teachers(id),
    classroom_id UUID REFERENCES school.classrooms(id),
    weekly_lessons INT NOT NULL DEFAULT 1,
    priority INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(school_class_id, subject_id)
);

CREATE TABLE IF NOT EXISTS school.timetable_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constraint_type TEXT NOT NULL,
    target_scope TEXT NOT NULL,
    target_id UUID,
    rule_code TEXT NOT NULL,
    rule_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    weight INT NOT NULL DEFAULT 10,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT timetable_constraint_type_check CHECK (constraint_type IN ('hard', 'soft'))
);

CREATE TABLE IF NOT EXISTS school.week_days (
    id SMALLSERIAL PRIMARY KEY,
    day_code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    sort_order INT NOT NULL UNIQUE
);

INSERT INTO school.week_days(day_code, name_ar, sort_order)
VALUES
('saturday', 'السبت', 1),
('sunday', 'الأحد', 2),
('monday', 'الإثنين', 3),
('tuesday', 'الثلاثاء', 4),
('wednesday', 'الأربعاء', 5),
('thursday', 'الخميس', 6)
ON CONFLICT (day_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS school.lesson_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_no INT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    starts_at TIME NOT NULL,
    ends_at TIME NOT NULL,
    is_break BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.timetable_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ar TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    effective_from DATE,
    effective_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.timetable_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_version_id UUID NOT NULL REFERENCES school.timetable_versions(id) ON DELETE CASCADE,
    school_class_id UUID NOT NULL REFERENCES school.school_classes(id),
    week_day_id SMALLINT NOT NULL REFERENCES school.week_days(id),
    period_id UUID NOT NULL REFERENCES school.lesson_periods(id),
    subject_name_ar TEXT NOT NULL,
    teacher_id UUID REFERENCES school.teachers(id),
    classroom_id UUID REFERENCES school.classrooms(id),
    slot_type TEXT NOT NULL DEFAULT 'lesson',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(timetable_version_id, school_class_id, week_day_id, period_id),

    CONSTRAINT timetable_slot_type_check
    CHECK (slot_type IN ('lesson', 'break', 'activity', 'empty'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_school_timetable_teacher_conflict
ON school.timetable_slots(timetable_version_id, teacher_id, week_day_id, period_id)
WHERE teacher_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_school_timetable_room_conflict
ON school.timetable_slots(timetable_version_id, classroom_id, week_day_id, period_id)
WHERE classroom_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS school.timetable_import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name TEXT NOT NULL,
    source_program TEXT NOT NULL DEFAULT 'TimeTable',
    source_format TEXT NOT NULL DEFAULT 'csv',
    total_rows INT NOT NULL DEFAULT 0,
    accepted_rows INT NOT NULL DEFAULT 0,
    rejected_rows INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'done',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.timetable_import_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES school.timetable_import_batches(id) ON DELETE CASCADE,
    row_number INT NOT NULL,
    row_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school.timetable_generation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_version_id UUID REFERENCES school.timetable_versions(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_cards INT NOT NULL DEFAULT 0,
    scheduled_lessons INT NOT NULL DEFAULT 0,
    conflict_count INT NOT NULL DEFAULT 0,
    quality_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS school.timetable_export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_version_id UUID REFERENCES school.timetable_versions(id) ON DELETE SET NULL,
    export_type TEXT NOT NULL DEFAULT 'csv',
    report_scope TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'done',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW school.vw_school_timetable_grid AS
SELECT
    slot.id,
    tv.id AS timetable_version_id,
    tv.name_ar AS timetable_name_ar,
    cls.class_code,
    cls.class_name_ar,
    wd.id AS week_day_id,
    wd.name_ar AS day_name_ar,
    wd.sort_order AS day_order,
    lp.period_no,
    lp.name_ar AS period_name_ar,
    lp.starts_at,
    lp.ends_at,
    slot.subject_name_ar,
    t.teacher_name_ar,
    room.room_name_ar,
    slot.slot_type,
    slot.notes
FROM school.timetable_slots slot
JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
JOIN school.school_classes cls ON cls.id = slot.school_class_id
JOIN school.week_days wd ON wd.id = slot.week_day_id
JOIN school.lesson_periods lp ON lp.id = slot.period_id
LEFT JOIN school.teachers t ON t.id = slot.teacher_id
LEFT JOIN school.classrooms room ON room.id = slot.classroom_id;

CREATE OR REPLACE VIEW school.vw_school_timetable_conflicts AS
WITH teacher_conflicts AS (
    SELECT
        'teacher'::text AS conflict_type,
        'hard'::text AS severity,
        timetable_version_id,
        teacher_id::text AS entity_id,
        week_day_id,
        period_id,
        count(*) AS conflict_count
    FROM school.timetable_slots
    WHERE teacher_id IS NOT NULL
    GROUP BY timetable_version_id, teacher_id, week_day_id, period_id
    HAVING count(*) > 1
),
room_conflicts AS (
    SELECT
        'room'::text AS conflict_type,
        'hard'::text AS severity,
        timetable_version_id,
        classroom_id::text AS entity_id,
        week_day_id,
        period_id,
        count(*) AS conflict_count
    FROM school.timetable_slots
    WHERE classroom_id IS NOT NULL
    GROUP BY timetable_version_id, classroom_id, week_day_id, period_id
    HAVING count(*) > 1
),
class_conflicts AS (
    SELECT
        'class'::text AS conflict_type,
        'hard'::text AS severity,
        timetable_version_id,
        school_class_id::text AS entity_id,
        week_day_id,
        period_id,
        count(*) AS conflict_count
    FROM school.timetable_slots
    GROUP BY timetable_version_id, school_class_id, week_day_id, period_id
    HAVING count(*) > 1
)
SELECT * FROM teacher_conflicts
UNION ALL
SELECT * FROM room_conflicts
UNION ALL
SELECT * FROM class_conflicts;

CREATE OR REPLACE VIEW school.vw_school_teacher_load AS
SELECT
    tv.id AS timetable_version_id,
    tv.name_ar AS timetable_name_ar,
    t.id AS teacher_id,
    t.teacher_name_ar,
    count(slot.id) FILTER (WHERE slot.slot_type = 'lesson') AS weekly_lessons_count
FROM school.teachers t
LEFT JOIN school.timetable_slots slot ON slot.teacher_id = t.id
LEFT JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
GROUP BY tv.id, tv.name_ar, t.id, t.teacher_name_ar;

CREATE OR REPLACE VIEW school.vw_school_timetable_quality AS
WITH version_stats AS (
    SELECT
        tv.id AS timetable_version_id,
        tv.name_ar AS timetable_name_ar,
        count(slot.id) AS scheduled_lessons,
        count(DISTINCT slot.school_class_id) AS classes_with_lessons,
        count(DISTINCT slot.teacher_id) FILTER (WHERE slot.teacher_id IS NOT NULL) AS teachers_used,
        count(DISTINCT slot.classroom_id) FILTER (WHERE slot.classroom_id IS NOT NULL) AS rooms_used
    FROM school.timetable_versions tv
    LEFT JOIN school.timetable_slots slot ON slot.timetable_version_id = tv.id
    GROUP BY tv.id, tv.name_ar
),
conflict_stats AS (
    SELECT timetable_version_id, count(*) AS hard_conflicts
    FROM school.vw_school_timetable_conflicts
    GROUP BY timetable_version_id
),
plan_stats AS (
    SELECT COALESCE(sum(weekly_lessons), 0)::int AS required_lessons
    FROM school.curriculum_plans
    WHERE is_active = true
)
SELECT
    vs.timetable_version_id,
    vs.timetable_name_ar,
    vs.scheduled_lessons,
    ps.required_lessons,
    COALESCE(cs.hard_conflicts, 0) AS hard_conflicts,
    GREATEST(
        0,
        LEAST(
            100,
            70
            + CASE WHEN ps.required_lessons > 0
                THEN ROUND((vs.scheduled_lessons::numeric / ps.required_lessons::numeric) * 30, 2)
                ELSE 0
              END
            - (COALESCE(cs.hard_conflicts, 0) * 30)
        )
    ) AS quality_score,
    jsonb_build_array(
        jsonb_build_object('code', 'coverage', 'message_ar', 'نسبة تغطية الخطة الأسبوعية'),
        jsonb_build_object('code', 'hard_conflicts', 'message_ar', 'خصم عند وجود تعارضات صارمة')
    ) AS reasons_json
FROM version_stats vs
CROSS JOIN plan_stats ps
LEFT JOIN conflict_stats cs ON cs.timetable_version_id = vs.timetable_version_id;

INSERT INTO core.migration_registry(migration_code, module_code, description_ar)
VALUES
('004_school_timetable_operational', 'timetable', 'تشغيل منصة الجداول المدرسية وربطها ببرنامج الموظفين والمدارس والتعارضات')
ON CONFLICT (migration_code) DO NOTHING;

UPDATE core.app_modules
SET status = 'operational'
WHERE code = 'timetable';
