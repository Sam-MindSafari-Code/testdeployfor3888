# data/import_projects_from_json.py
import json
from pathlib import Path
from typing import List, Dict, Any
from data.db_connection import get_conn

TABLE_NAME = '"Project_List"'
JSON_PATH_DEFAULT = "data/projects.json"

def _coalesce_list_str(lst: List[str] | None) -> str:
    if not lst:
        return ""
    cleaned = [s.strip() for s in lst if s and s.strip()]
    return ";".join(cleaned)

def import_projects_from_json(
    json_path: str = JSON_PATH_DEFAULT,
    table_name: str = TABLE_NAME,
    replace_all: bool = True,
) -> None:
    path = Path(json_path)
    projects: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    rows = []
    for p in projects:
        project_id = p.get("id")
        if not project_id:
            continue
        rows.append((
            project_id,
            p.get("title"),
            p.get("client"),
            _coalesce_list_str(p.get("required_skills")),
            _coalesce_list_str(p.get("related_disciplines")),
        ))

    if not rows:
        print("No valid project rows found in JSON; aborting.")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if replace_all:
                cur.execute(f'TRUNCATE TABLE {table_name};')
            sql = f"""
            INSERT INTO {table_name}
                (project_id, title, client, required_skills, related_disciplines)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (project_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                client = EXCLUDED.client,
                required_skills = EXCLUDED.required_skills,
                related_disciplines = EXCLUDED.related_disciplines;
            """
            cur.executemany(sql, rows)

        conn.commit()
        print(f"Imported {len(rows)} projects into {table_name} (replace_all={replace_all})")
    finally:
        conn.close()

if __name__ == "__main__":
    import_projects_from_json()
