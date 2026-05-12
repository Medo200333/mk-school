from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


ROOT = Path("external/access_analysis")
INVENTORY = ROOT / "01_business_tables_inventory.json"

DB_URL = os.environ.get(
    "MK_PG_DSN",
    "postgresql://mk_user:mk_password@localhost:55433/mk_school",
)

SYSTEM_TABLE_PREFIXES = ("MSys", "USys")
SYSTEM_TABLE_NAMES = {
    "MSysAccessStorage",
    "MSysAccessXML",
    "MSysIMEXSpecs",
    "MSysIMEXColumns",
    "MSysNavPaneGroupCategories",
    "MSysNavPaneGroups",
    "MSysNavPaneGroupToObjects",
    "MSysNavPaneObjectIDs",
    "MSysResources",
    "MSysNameMap",
    "USysRibbons",
}

SUBJECT_HINTS = {
    "qran": "قرآن كريم",
    "qrant": "قرآن تحريري",
    "qransh": "قرآن شفوي",
    "araba": "لغة عربية",
    "arab": "لغة عربية",
    "deen": "تربية دينية",
    "math": "رياضيات",
    "olom": "علوم",
    "en": "لغة إنجليزية",
    "darast": "دراسات اجتماعية",
    "tecnolog": "تكنولوجيا",
    "mhara": "مهارات مهنية",
    "qyma": "قيم واحترام الآخر",
    "rasm": "تربية فنية",
    "trbyryadya": "تربية رياضية",
    "tokatsoa": "توكاتسو",
    "mosa": "مستوى رفيع / نشاط",
    "fkh": "فقه",
    "tfser": "تفسير",
    "hadth": "حديث",
    "hdth": "حديث",
    "twhed": "توحيد",
    "nho": "نحو",
    "srf": "صرف",
    "motal": "مطالعة ونصوص",
    "gbr": "جبر",
    "hndsa": "هندسة",
    "comt": "حاسب تحريري",
    "comsh": "حاسب شفوي",
    "qraat": "قراءات",
    "mntk": "منطق",
    "blagha": "بلاغة",
    "ensha": "إنشاء",
    "adb": "أدب",
    "traq": "تاريخ",
    "gogh": "جغرافيا",
    "thqeslam": "ثقافة إسلامية",
    "nafs": "علم نفس",
    "orod": "عروض",
    "phlosphy": "فلسفة",
    "moatna": "مواطنة",
    "tfadl": "تفاضل",
    "handhesah": "هندسة",
    "tatmath": "تطبيقات رياضيات",
    "fzya": "فيزياء",
    "kmaya": "كيمياء",
    "ahya": "أحياء",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).encode("utf-8", errors="backslashreplace").decode("utf-8", errors="replace")


def is_system_table(name: str) -> bool:
    return name in SYSTEM_TABLE_NAMES or name.startswith(SYSTEM_TABLE_PREFIXES)


def safe_table_name(table: str) -> str:
    table = table.translate(str.maketrans(' /:*?"<>|', "_________"))
    allowed = "._-أإآابتثجحخدذرزسشصضطظعغفقكلمنهويىءؤئلاة0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(ch for ch in table if ch in allowed or ch.isalnum())


def table_csv_path(database_dir_name: str, table_name: str) -> Path:
    return ROOT / database_dir_name / f"table_{safe_table_name(table_name)}.csv"


def detect_subject(column: str) -> tuple[str, str, str]:
    col = column.lower().strip()

    component = "unknown"
    if "mham" in col:
        component = "مهام أدائية"
    elif "moazba" in col:
        component = "مواظبة / سلوك"
    elif "sh" in col or "shf" in col:
        component = "شفوي"
    elif re.search(r"\d$", col):
        component = "درجة / اختبار"
    elif col.endswith("b") or col.endswith("c"):
        component = "مرحلة / صف"
    elif col.endswith("t"):
        component = "تحريري"

    normalized = re.sub(r"\d+", "", col)
    normalized = normalized.replace("mham", "")
    normalized = normalized.replace("moazba", "")
    normalized = normalized.rstrip("abc")
    normalized = normalized.strip("_")

    subject_name = "غير مصنف"
    subject_code = normalized or col

    for key, name in sorted(SUBJECT_HINTS.items(), key=lambda x: len(x[0]), reverse=True):
        if subject_code.startswith(key) or key in subject_code:
            subject_name = name
            subject_code = key
            break

    return subject_code, subject_name, component


DDL = """
CREATE SCHEMA IF NOT EXISTS education_control_access;

CREATE TABLE IF NOT EXISTS education_control_access.import_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_root TEXT NOT NULL,
    inventory_file TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS education_control_access.raw_databases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_database TEXT NOT NULL UNIQUE,
    source_path TEXT,
    tables_count INT NOT NULL DEFAULT 0,
    business_tables_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS education_control_access.raw_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_database_id UUID NOT NULL REFERENCES education_control_access.raw_databases(id) ON DELETE CASCADE,
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    classification TEXT,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    rows_count INT NOT NULL DEFAULT 0,
    columns_count INT NOT NULL DEFAULT 0,
    columns_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    sample_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_database, source_table)
);

CREATE TABLE IF NOT EXISTS education_control_access.raw_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_table_id UUID NOT NULL REFERENCES education_control_access.raw_tables(id) ON DELETE CASCADE,
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_column TEXT NOT NULL,
    ordinal_position INT NOT NULL,
    detected_subject_code TEXT,
    detected_subject_name_ar TEXT,
    detected_component TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(raw_table_id, source_column)
);

CREATE TABLE IF NOT EXISTS education_control_access.raw_rows (
    id BIGSERIAL PRIMARY KEY,
    raw_table_id UUID NOT NULL REFERENCES education_control_access.raw_tables(id) ON DELETE CASCADE,
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_number INT NOT NULL,
    row_hash TEXT NOT NULL,
    row_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(raw_table_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS education_control_access.material_column_dictionary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_table_id UUID REFERENCES education_control_access.raw_tables(id) ON DELETE CASCADE,
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_column TEXT NOT NULL,
    normalized_subject_code TEXT NOT NULL,
    subject_name_ar TEXT NOT NULL,
    score_component TEXT NOT NULL,
    stage_hint TEXT,
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_database, source_table, source_column)
);

CREATE TABLE IF NOT EXISTS education_control_access.table_link_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_role TEXT NOT NULL,
    target_schema TEXT NOT NULL,
    target_table TEXT NOT NULL,
    link_strategy TEXT NOT NULL,
    confidence NUMERIC(5,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_database, source_table, source_role)
);

CREATE INDEX IF NOT EXISTS ix_access_raw_rows_table ON education_control_access.raw_rows(raw_table_id);
CREATE INDEX IF NOT EXISTS ix_access_raw_rows_data_gin ON education_control_access.raw_rows USING GIN(row_data);
CREATE INDEX IF NOT EXISTS ix_access_raw_columns_table ON education_control_access.raw_columns(raw_table_id);
CREATE INDEX IF NOT EXISTS ix_access_material_subject ON education_control_access.material_column_dictionary(normalized_subject_code);
"""


def parse_int(value: Any) -> int:
    try:
        if value in (None, "", "unknown", "export_failed"):
            return 0
        return int(str(value))
    except Exception:
        return 0


def row_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8", errors="backslashreplace")).hexdigest()


def seed_link_rules(cur: psycopg.Cursor) -> None:
    rules = [
        ("studen", "students", "school", "students", "legacy_access_id/name matching", 0.95, "جدول الطالب المرشح الأساسي."),
        ("data_xlsx", "student_excel_import", "education_control_access", "raw_rows", "raw import snapshot", 0.85, "جدول استيراد Excel."),
        ("data_xlsx0", "student_excel_import", "education_control_access", "raw_rows", "raw import snapshot", 0.85, "جدول استيراد Excel إضافي."),
        ("z_Countries", "countries_lookup", "school", "students", "lookup normalization", 0.80, "مرجع الدول/الجنسية."),
        ("z_gender", "gender_lookup", "school", "students", "lookup normalization", 0.90, "مرجع النوع."),
        ("z_marhala", "education_stage_lookup", "school", "grades", "lookup normalization", 0.90, "مرجع المرحلة."),
        ("z_row", "grade_lookup", "school", "grades", "lookup normalization", 0.90, "مرجع الصف."),
        ("z_section", "section_lookup", "school", "grades", "lookup normalization", 0.85, "مرجع القسم/الشعبة."),
        ("z_reg", "religion_lookup", "school", "students", "lookup normalization", 0.80, "مرجع الديانة."),
        ("z_national", "nationality_lookup", "school", "students", "lookup normalization", 0.80, "مرجع الجنسية."),
        ("z_helth", "health_lookup", "school", "students", "lookup normalization", 0.80, "مرجع الحالة الصحية."),
        ("z_helthex", "health_exception_lookup", "school", "students", "lookup normalization", 0.80, "مرجع استثناءات صحية."),
        ("z_insttip", "institute_type_lookup", "school", "institutes", "lookup normalization", 0.85, "نوع المعهد."),
        ("z_instuat", "institute_lookup", "school", "institutes", "lookup normalization", 0.85, "بيانات المعاهد."),
        ("z_edarat", "administration_lookup", "school", "institutes", "lookup normalization", 0.80, "الإدارات التعليمية."),
        ("z_zon", "zone_lookup", "school", "institutes", "lookup normalization", 0.80, "المناطق."),
        ("stander", "score_standards", "education_control", "subjects", "subject/max/min mapping", 0.75, "إعدادات معيارية للدرجات."),
        ("rsd2nd", "second_round_scores", "education_control", "score_entries", "second round score mapping", 0.90, "رصد الدور الثاني."),
        ("nsba", "percentage_rules", "education_control", "results", "percentage calculation mapping", 0.85, "قواعد النسبة."),
        ("chose", "selection_options", "education_control", "exam_terms", "settings mapping", 0.70, "اختيارات تشغيل."),
        ("ud", "activation_settings", "education_control", "activation_settings", "activation code mapping", 0.95, "ملفات التفعيل: 111/222/333."),
    ]

    for source_table, role, schema, table, strategy, confidence, notes in rules:
        cur.execute(
            """
            INSERT INTO education_control_access.table_link_rules
            (source_database, source_table, source_role, target_schema, target_table, link_strategy, confidence, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_database, source_table, source_role)
            DO UPDATE SET
              target_schema = EXCLUDED.target_schema,
              target_table = EXCLUDED.target_table,
              link_strategy = EXCLUDED.link_strategy,
              confidence = EXCLUDED.confidence,
              notes = EXCLUDED.notes
            """,
            ("*", source_table, role, schema, table, strategy, confidence, notes),
        )


def main() -> None:
    if not INVENTORY.exists():
        raise SystemExit(f"Missing inventory file: {INVENTORY}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8", errors="replace"))

    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
            cur.execute(DDL)

            cur.execute(
                """
                INSERT INTO education_control_access.import_runs(source_root, inventory_file)
                VALUES (%s, %s)
                RETURNING id
                """,
                (str(ROOT), str(INVENTORY)),
            )
            run_id = cur.fetchone()["id"]

            cur.execute("TRUNCATE education_control_access.raw_rows RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE education_control_access.table_link_rules CASCADE")
            cur.execute("TRUNCATE education_control_access.raw_databases CASCADE")

            db_groups: dict[str, list[dict[str, Any]]] = {}
            for item in inventory:
                db_groups.setdefault(clean_text(item["database"]), []).append(item)

            for database_name, items in db_groups.items():
                source_path = clean_text(items[0].get("database_path", ""))
                tables_count = len(items)
                business_count = sum(1 for item in items if not item.get("is_system"))

                cur.execute(
                    """
                    INSERT INTO education_control_access.raw_databases
                    (source_database, source_path, tables_count, business_tables_count)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (database_name, source_path, tables_count, business_count),
                )
                raw_database_id = cur.fetchone()["id"]

                for item in items:
                    source_table = clean_text(item["table"])
                    columns = [clean_text(c) for c in item.get("columns", [])]
                    samples = item.get("sample_rows", [])
                    rows_count = parse_int(item.get("rows"))
                    classification = clean_text(item.get("classification", ""))
                    is_system = bool(item.get("is_system"))

                    cur.execute(
                        """
                        INSERT INTO education_control_access.raw_tables
                        (raw_database_id, source_database, source_table, classification, is_system,
                         rows_count, columns_count, columns_json, sample_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                        RETURNING id
                        """,
                        (
                            raw_database_id,
                            database_name,
                            source_table,
                            classification,
                            is_system,
                            rows_count,
                            len(columns),
                            json.dumps(columns, ensure_ascii=False),
                            json.dumps(samples, ensure_ascii=False),
                        ),
                    )
                    raw_table_id = cur.fetchone()["id"]

                    for idx, column in enumerate(columns, start=1):
                        sub_code, sub_name, component = detect_subject(column)
                        cur.execute(
                            """
                            INSERT INTO education_control_access.raw_columns
                            (raw_table_id, source_database, source_table, source_column,
                             ordinal_position, detected_subject_code, detected_subject_name_ar, detected_component)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (raw_table_id, source_column) DO NOTHING
                            """,
                            (raw_table_id, database_name, source_table, column, idx, sub_code, sub_name, component),
                        )

                        if sub_name != "غير مصنف":
                            cur.execute(
                                """
                                INSERT INTO education_control_access.material_column_dictionary
                                (raw_table_id, source_database, source_table, source_column,
                                 normalized_subject_code, subject_name_ar, score_component, stage_hint)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (source_database, source_table, source_column)
                                DO UPDATE SET
                                  normalized_subject_code = EXCLUDED.normalized_subject_code,
                                  subject_name_ar = EXCLUDED.subject_name_ar,
                                  score_component = EXCLUDED.score_component,
                                  stage_hint = EXCLUDED.stage_hint
                                """,
                                (
                                    raw_table_id,
                                    database_name,
                                    source_table,
                                    column,
                                    sub_code,
                                    sub_name,
                                    component,
                                    classification,
                                ),
                            )

                    csv_path = table_csv_path(database_name, source_table)

                    if csv_path.exists() and rows_count > 0:
                        with csv_path.open("r", encoding="utf-8", errors="backslashreplace", newline="") as f:
                            reader = csv.DictReader(f)
                            batch = []
                            for row_number, row in enumerate(reader, start=1):
                                clean_row = {clean_text(k): clean_text(v) for k, v in row.items()}
                                batch.append(
                                    (
                                        raw_table_id,
                                        database_name,
                                        source_table,
                                        row_number,
                                        row_hash(clean_row),
                                        json.dumps(clean_row, ensure_ascii=False),
                                    )
                                )

                                if len(batch) >= 1000:
                                    cur.executemany(
                                        """
                                        INSERT INTO education_control_access.raw_rows
                                        (raw_table_id, source_database, source_table, source_row_number, row_hash, row_data)
                                        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                                        ON CONFLICT (raw_table_id, source_row_number)
                                        DO UPDATE SET row_hash = EXCLUDED.row_hash, row_data = EXCLUDED.row_data
                                        """,
                                        batch,
                                    )
                                    batch.clear()

                            if batch:
                                cur.executemany(
                                    """
                                    INSERT INTO education_control_access.raw_rows
                                    (raw_table_id, source_database, source_table, source_row_number, row_hash, row_data)
                                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                                    ON CONFLICT (raw_table_id, source_row_number)
                                    DO UPDATE SET row_hash = EXCLUDED.row_hash, row_data = EXCLUDED.row_data
                                    """,
                                    batch,
                                )

            seed_link_rules(cur)

            cur.execute(
                """
                UPDATE education_control_access.import_runs
                SET finished_at = now(),
                    status = 'done',
                    payload = %s::jsonb
                WHERE id = %s
                """,
                (
                    json.dumps(
                        {
                            "databases": len(db_groups),
                            "tables": len(inventory),
                        },
                        ensure_ascii=False,
                    ),
                    run_id,
                ),
            )

        conn.commit()

    print("✅ Access full mirror imported into PostgreSQL")
    print(f"✅ inventory tables: {len(inventory)}")


if __name__ == "__main__":
    main()
