from typing import List, Dict, Any
from app.models import Group
from app import scoring_helpers, save_load


WEIGHTS = {
    "preference": 0.4,
    "skills": 0.3,
    "wam": 0.2,
    "dual_group": -0.1
}

def match_projects(
    groups_data: List[Group],
    projects_table: str = save_load.PROJECTS_TABLE,
    save_to_db: bool = True
) -> Dict[str, Any]:

    PROJECTS = save_load.load_projects_from_db(projects_table)

    allocations = {}
    assigned_projects = set()

    # summary trackers for dashboard later on
    project_demand = {project["id"]: 0 for project in PROJECTS}
    skill_totals = {skill: 0 for skill in scoring_helpers.skill_ratings}
    total_pref_scores = 0
    total_skill_scores = 0
    total_wam_scores = 0
    dual_count = 0

    i = 0
    while i < len(groups_data):
        group = groups_data[i]
        best_project = None
        best_score = -1

        x = 0
        while x < len(PROJECTS):
            project = PROJECTS[x]
            if project["id"] in assigned_projects:
                x += 1
                continue

            # scoring logic is now done in scoring_helpers
            preference_score = scoring_helpers.calculate_preference_score(group.project_preferences, project["id"])
            skills_score = scoring_helpers.calculate_skills_score(group.skills, project["required_skills"])
            wam_score = scoring_helpers.calculate_wam_score(group.wam_breakdown)
            dual_group = WEIGHTS["dual_group"] if group.dual_project_enrollment else 0

            total_score = (
                preference_score * WEIGHTS["preference"] +
                skills_score * WEIGHTS["skills"] +
                wam_score * WEIGHTS["wam"] +
                dual_group
            )

            if total_score > best_score:
                best_score = total_score
                best_project = project["id"]
            x += 1

        if best_project:
            allocations[group.group_id] = best_project
            assigned_projects.add(best_project)
        
        # update summary stats for dashboard later on
        for pref in group.project_preferences:
            if pref in project_demand:
                project_demand[pref] += 1
        
        for skill in group.skills:
            if skill in skill_totals:
                skill_totals[skill] += 1

        total_pref_scores += preference_score
        total_skill_scores += skills_score
        total_wam_scores += wam_score
        if group.dual_project_enrollment:
            dual_count += 1

        i += 1

    # added skill coverage and average score calcs
    total_groups = len(groups_data)
    skill_coverage = {
        k: round(v / total_groups, 2) for k, v in skill_totals.items()
    }

    summary = {
        "project_demand": project_demand,
        "skill_coverage": skill_coverage,
        "average_preference_score": round(total_pref_scores / total_groups, 3),
        "average_skills_score": round(total_skill_scores / total_groups, 3),
        "average_wam_score": round(total_wam_scores / total_groups, 3),
        "dual_project_count": dual_count
    }

    # saving allocations results to db before returning
    if save_to_db and allocations:
        save_load.save_allocations_to_db(
            allocations,
            table_fullname='"Allocation_Results"', 
            upsert=True,
            replace_all=False
        )

    if save_to_db and summary:
        save_load.save_summary_to_db(
            summary,
            summary_table='"Allocation_Summary"',
            demand_table='"Project_Demand"',
            skill_table='"Skill_Coverage"',
            replace_all=True
        )

    # added both allocation and summary making the output better/detailed and mainly for dashboard.
    return {
        "allocations": allocations,
        "summary": summary
    }

