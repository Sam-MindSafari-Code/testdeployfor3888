
# app/save_load.py
from typing import Any, List, Dict, Tuple
from data.db_connection import get_conn, fetch_all_dicts

PROJECTS_TABLE = '"Project_List"'
ALLOC_TABLE = '"Allocation_Results"'



def normalize_required_skills(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value]

    s = str(value).strip()
    if not s:
        return []
    try:
        import json
        parsed = json.loads(s)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed]
    except Exception:
        pass
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    return [p for p in parts if p]


def load_projects_from_db(table_fullname: str = PROJECTS_TABLE) -> List[Dict[str, Any]]:
    sql = f"""
        SELECT project_id AS id, required_skills
        FROM {table_fullname}
    """
    rows = fetch_all_dicts(sql)
    projects: List[Dict[str, Any]] = []
    for r in rows:
        p = dict(r)
        p["id"] = str(p.get("id"))
        p["required_skills"] = normalize_required_skills(p.get("required_skills"))
        projects.append(p)
    return projects


def save_allocations_to_db(
    allocations: Dict[str, str],
    table_fullname: str = ALLOC_TABLE,
    upsert: bool = True,
    replace_all: bool = False,
):
    if not allocations:
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_fullname} (
                group_id   TEXT PRIMARY KEY,
                project_id TEXT NOT NULL
            );
            """)

            if replace_all:
                cur.execute(f"TRUNCATE TABLE {table_fullname};")

            if upsert:
                sql = f"""
                INSERT INTO {table_fullname} (group_id, project_id)
                VALUES (%s, %s)
                ON CONFLICT (group_id)
                DO UPDATE SET project_id = EXCLUDED.project_id;
                """
            else:
                sql = f'INSERT INTO {table_fullname} (group_id, project_id) VALUES (%s, %s);'

            params = [(gid, pid) for gid, pid in allocations.items()]
            cur.executemany(sql, params)

        conn.commit()
    finally:
        conn.close()



def load_summary_from_db() -> Dict[str, Any]:
    summary_rows = fetch_all_dicts(
        'SELECT average_preference_score, average_skills_score, average_wam_score, dual_project_count '
        'FROM "Allocation_Summary" ORDER BY id DESC LIMIT 1;'
    )
    if not summary_rows:
        return {} 

    summary: Dict[str, Any] = dict(summary_rows[0])

    demand_rows = fetch_all_dicts('SELECT project_id, chosen_count FROM "Project_Demand";')
    summary["project_demand"] = {r["project_id"]: r["chosen_count"] for r in demand_rows}

    skill_rows = fetch_all_dicts('SELECT skill_name, skill_percentage FROM "Skill_Coverage";')
    summary["skill_coverage"] = {r["skill_name"]: float(r["skill_percentage"]) for r in skill_rows}

    return summary


def save_summary_to_db(
    summary: Dict[str, Any],
    summary_table: str = '"Allocation_Summary"',
    demand_table: str = '"Project_Demand"',
    skill_table: str = '"Skill_Coverage"',
    replace_all: bool = True
) -> None:
    if not summary:
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1) Allocation_Summary
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {summary_table} (
                    id SERIAL PRIMARY KEY,
                    average_preference_score FLOAT,
                    average_skills_score    FLOAT,
                    average_wam_score       FLOAT,
                    dual_project_count      INT
                );
            ''')

            cur.execute(
                f'''
                INSERT INTO {summary_table}
                (average_preference_score, average_skills_score, average_wam_score, dual_project_count)
                VALUES (%s, %s, %s, %s);
                ''',
                (
                    summary.get("average_preference_score"),
                    summary.get("average_skills_score"),
                    summary.get("average_wam_score"),
                    summary.get("dual_project_count"),
                ),
            )

            # 2) Project_Demand
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {demand_table} (
                    project_id   TEXT PRIMARY KEY,
                    chosen_count INT NOT NULL
                );
            ''')
            if replace_all:
                cur.execute(f'TRUNCATE TABLE {demand_table};')

            demand_rows: List[Tuple[str, int]] = [
                (pid, int(count)) for pid, count in (summary.get("project_demand") or {}).items()
            ]
            if demand_rows:
                cur.executemany(
                    f'''
                    INSERT INTO {demand_table} (project_id, chosen_count)
                    VALUES (%s, %s)
                    ON CONFLICT (project_id) DO UPDATE
                    SET chosen_count = EXCLUDED.chosen_count;
                    ''',
                    demand_rows,
                )

            # 3) Skill_Coverage
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {skill_table} (
                    skill_name       TEXT PRIMARY KEY,
                    skill_percentage FLOAT NOT NULL
                );
            ''')
            if replace_all:
                cur.execute(f'TRUNCATE TABLE {skill_table};')

            skill_rows: List[Tuple[str, float]] = [
                (name, float(pct)) for name, pct in (summary.get("skill_coverage") or {}).items()
            ]
            if skill_rows:
                cur.executemany(
                    f'''
                    INSERT INTO {skill_table} (skill_name, skill_percentage)
                    VALUES (%s, %s)
                    ON CONFLICT (skill_name) DO UPDATE
                    SET skill_percentage = EXCLUDED.skill_percentage;
                    ''',
                    skill_rows,
                )

        conn.commit()
    finally:
        conn.close()