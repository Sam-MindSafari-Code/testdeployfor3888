# app/models.py

from pydantic import BaseModel
from typing import List, Dict, Optional

class Student(BaseModel):
    name: str
    student_id: str
    unikey: str
    unit_code: str
    wam: float
    group_id: Optional[str] = None
    tutor_code: str
    dual_project_enrollment: bool
    skills: List[str]
    project_preferences: List[str]

class Group(BaseModel):
    group_id: str
    students: List[Student]
    project_preferences: List[str]
    wam_breakdown: Dict[str, int]
    dual_project_enrollment: bool
    skills: List[str]
    justification: str

class AllocationSummary(BaseModel):
    project_demand: Dict[str, int]
    skill_coverage: Dict[str, float]
    average_preference_score: float
    average_skills_score: float
    average_wam_score: float
    dual_project_count: int

class AllocationResult(BaseModel):
    allocations: Dict[str, str]   
    summary: AllocationSummary