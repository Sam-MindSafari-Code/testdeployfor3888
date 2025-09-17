# scoring_helpers.py contains modular scoring functions used to evaluate
# project allocations based on preferences, skills, and WAM all normalised to a 0-1 scale.
# using raw sclae like 1-4 first allows for more flexibility and control as we can emphaisise a grade more and allows us more control over grade weighting (so if client says HD should have more impact we can easily adjust) cleaner math as well 
# These are used by the matching algorithm in algorithm.py
# wanted to implement linear skill rating adds more depth to the calcualion and we can justify as well since computer science capstone assumptions were made on what skills are neeeded based on degree capstone graduate qualities

skill_ratings = {
    "Web Development": 4,
    "Database": 4,
    "Algorithms": 4,
    "Data Science/Analytics/Visualisation": 3,
    "UI/UX": 3,
    "Cloud Computing (AWS/AZURE/GCP)": 3,
    "Image Processing/ Segmentation": 2,
    "Machine learning /Deep Learning": 4,
    "Python": 4,
    "Data analysis": 3,
}
wam_weights = {
    "HD": 4,
    "D": 3,
    "C": 2,
    "P": 1,
}

def calculate_preference_score(preferences, project_id):
    try:
        rank = preferences.index(project_id)
        return 1 - (rank / len(preferences))
    except ValueError:
        return 0

def calculate_skills_score(group_skills, project_skills):
    score = 0
    for skill in project_skills:
        if skill in group_skills:
            score += skill_ratings.get(skill, 0)
            # matches = set(group_skills) & set(project_skills) # commented out because doesnt account for weights of skills as its flat match ratio
           # return len(matches) / len(project_skills) if project_skills else 0
    max_score = len(project_skills) * 5
    return score / max_score if max_score else 0

def calculate_wam_score(wam_breakdown):
    total = sum(wam_breakdown.values())
    if total == 0:
        return 0
    weighted_score = sum(wam_weights.get(k, 0) * v for k, v in wam_breakdown.items())
    return weighted_score / (total * 4)  # normalise into the 0-1 scale 