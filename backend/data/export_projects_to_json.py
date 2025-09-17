from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

from .db_connection import fetch_all_dicts

OUT_PATH = Path(__file__).parent / "projects.json"

# normalize skill names(allow add or modyfy)
CANON = {
    "ml": "ML",
    "dl": "DL",
    "ai": "AI",
    "cv": "CV",
    "pytorch": "PyTorch",
    "pyTorch": "PyTorch",
    "db": "Database",
    "sql": "Database",
    "uiux": "UI/UX",
    "ui/ux": "UI/UX",
    "web dev": "Web Development",
    "web": "Web Development",
    "js": "JavaScript",
}

def split_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        items = [str(i).strip() for i in x]
    else:
        s = str(x)
        parts = (s.split(";") if ";" in s else s.replace("|", ",").split(","))
        items = [p.strip() for p in parts]
    seen, out = set(), []
    for it in items:
        if not it:
            continue
        it2 = CANON.get(it.lower(), it)
        if it2 not in seen:
            seen.add(it2)
            out.append(it2)
    return out

def export_projects() -> None:
    rows = fetch_all_dicts(
        'SELECT project_id, title, client, required_skills, related_disciplines '
        'FROM "Project_List" ORDER BY project_id;'
    )
    bucket: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pid = r["project_id"]
        proj = bucket.setdefault(pid, {
            "id": pid,
            "title": r.get("title"),
            "client": r.get("client"),
            "required_skills": [],
            "related_disciplines": [],
        })
        for key in ("required_skills", "related_disciplines"):
            existing = set(proj[key])
            for v in split_list(r.get(key)):
                if v not in existing:
                    proj[key].append(v)
                    existing.add(v)

    data = [bucket[k] for k in sorted(bucket.keys())]
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data)} projects to {OUT_PATH}")

if __name__ == "__main__":
    export_projects()