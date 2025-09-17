# data/import_students_from_json.py
import json
from pathlib import Path
from typing import List, Dict, Any
from data.db_connection import get_conn

TABLE_NAME = '"Student"'
JSON_PATH_DEFAULT = "data/students.json"


def _coalesce_list_str(lst: List[str] | None) -> str:
    if not lst:
        return ""
    cleaned = [s.strip() for s in lst if s and s.strip()]
    return ";".join(cleaned)


def import_students_from_json(
        json_path: str = JSON_PATH_DEFAULT,
        table_name: str = TABLE_NAME,
        replace_all: bool = True,
) -> None:
    path = Path(json_path)
    students: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    rows = []
    for s in students:
        student_id = s.get("student_id")
        if not student_id:
            continue
        rows.append((
            int(student_id),
            s.get("name"),
            s.get("unikey"),
            s.get("unit_code"),
            str(s.get("wam")) if s.get("wam") is not None else None,
            _coalesce_list_str(s.get("skills")),
            s.get("dual_project_enrollment", False),
            s.get("group_id"),
            s.get("tutor_code"),
            _coalesce_list_str(s.get("project_preferences")),
        ))

    if not rows:
        print("No valid student rows found in JSON; aborting.")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if replace_all:
                cur.execute(f'TRUNCATE TABLE {table_name};')
            sql = f"""
            INSERT INTO {table_name}
                (student_id, name, unikey, unit_code, wam, skill, dual_project_enrollment, group_name, tutor_code, project_preferences)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (student_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                unikey = EXCLUDED.unikey,
                unit_code = EXCLUDED.unit_code,
                wam = EXCLUDED.wam,
                skill = EXCLUDED.skill,
                dual_project_enrollment = EXCLUDED.dual_project_enrollment,
                group_name = EXCLUDED.group_name,
                tutor_code = EXCLUDED.tutor_code,
                project_preferences = EXCLUDED.project_preferences;
            """
            cur.executemany(sql, rows)

        conn.commit()
        print(f"Imported {len(rows)} students into {table_name} (replace_all={replace_all})")
    finally:
        conn.close()


if __name__ == "__main__":
    import_students_from_json()