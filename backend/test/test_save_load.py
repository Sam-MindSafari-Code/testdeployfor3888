import json
from pathlib import Path
from typing import Any, Dict, List
from app.algorithm import match_projects
from app.models import Group
from app import save_load
from data.db_connection import fetch_all_dicts, get_conn

JSON_PATH = Path(__file__).resolve().parents[1] / "data" / "example_backend_input.json"

PROJECTS_TABLE = save_load.PROJECTS_TABLE


def ensure_projects_exist(project_ids: List[str], table: str) -> None:
    if not project_ids:
        return
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    project_id TEXT PRIMARY KEY,
                    required_skills TEXT
                );
            ''')
            rows = [(pid, '["Web Development","Database","UI/UX"]') for pid in sorted(set(project_ids))]
            cur.executemany(
                f'''INSERT INTO {table} (project_id, required_skills)
                    VALUES (%s, %s)
                    ON CONFLICT (project_id) DO NOTHING;''',
                rows
            )
        conn.commit()
    finally:
        conn.close()


def load_groups_for_pydantic(path: Path) -> List[Group]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for g in data["groups"]:
        for s in g.get("students", []):
            s.setdefault("tutor_code", "T01")
            s.setdefault("project_preferences", [])
    return [Group(**g) for g in data["groups"]]


if __name__ == "__main__":
    groups = load_groups_for_pydantic(JSON_PATH)

    project_ids = []
    for g in groups:
        project_ids.extend(g.project_preferences)
    ensure_projects_exist(project_ids, PROJECTS_TABLE)

    result = match_projects(groups, projects_table=PROJECTS_TABLE, save_to_db=True)
    print("Allocations:", result["allocations"])
    print("Summary keys:", list(result["summary"].keys()))

    alloc_rows = fetch_all_dicts('SELECT group_id, project_id FROM "Allocation_Results" ORDER BY group_id;')
    assert alloc_rows, "Allocation_Results has no data"
    print("✅ Allocation_Results rows:", alloc_rows)

    summary_row = fetch_all_dicts(
        'SELECT id, average_wam_score FROM "Allocation_Summary" ORDER BY id DESC LIMIT 1;'
    )
    assert summary_row, "Allocation_Summary has no data"
    print("✅ Allocation_Summary latest:", summary_row[0])

    demand_rows = fetch_all_dicts('SELECT project_id, chosen_count FROM "Project_Demand";')
    assert demand_rows, "Project_Demand has no data"
    print("✅ Project_Demand sample:", demand_rows[:5])

    skill_rows = fetch_all_dicts('SELECT skill_name, skill_percentage FROM "Skill_Coverage";')
    assert skill_rows, "Skill_Coverage has no data"
    print("✅ Skill_Coverage sample:", skill_rows[:5])
