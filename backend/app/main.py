from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi import Depends
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import Body
from fastapi import Request
from fastapi import Response
from fastapi import Form
import json
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import RedirectResponse, JSONResponse


app = FastAPI()

# Avoid startup crash if /static isn't visible at cold start
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir, check_dir=False), name="static")

@app.get("/health", include_in_schema=False)
async def health():
    return JSONResponse({"ok": True})

@app.get("/", include_in_schema=False) # did this because for some reason in terminal the link didn't take me directly to docs
async def redirect_to_docs():
    return RedirectResponse(url="/login", status_code=302)

# Load users
def load_users():
    json_path = Path(__file__).parent.parent / "data" / "users.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Check login + role
def get_current_user(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"username": username, "role": role}

def admin_only(request: Request):
    role = request.cookies.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    
@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 403:
        return RedirectResponse(url="/not-authorized", status_code=303)
    if exc.status_code == 401:
        return RedirectResponse(url="/login", status_code=303)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.get("/not-authorized", include_in_schema=False)
async def serve_not_authorized():
    html_path = Path(__file__).parent / "static" / "not_authorized.html"
    return FileResponse(html_path)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return 204 so browsers stop retrying if you don't have a favicon file bundled
    return Response(status_code=204)

# Login endpoint
@app.post("/login-check")
async def login(username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    users = load_users()
    user = next((u for u in users if u["username"] == username and u["password"] == password), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user["role"] != role:
        raise HTTPException(status_code=403, detail="Unauthorized role for this login")
    
    response = RedirectResponse(
        url="/admin" if user["role"] == "admin" else "/projectList", 
        status_code=303
    )
    response.set_cookie(key="username", value=user["username"])
    response.set_cookie(key="role", value=user["role"])
    return response

@app.get("/login", include_in_schema=False)
async def serve_login_page():
    html_path = Path(__file__).parent / "static" / "login.html"
    if not html_path.exists():
        # Helpful debug: report what path the function is trying to read
        return JSONResponse(
            {"error": "login.html not found", "looked_for": str(html_path)},
            status_code=500
        )
    return FileResponse(html_path)


# Logout
@app.get("/logout", include_in_schema=False)
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("username", path="/")
    response.delete_cookie("role", path="/")
    return response

#Student page
@app.get("/projectList", include_in_schema=False)
async def serve_project_list():
    html_path = Path(__file__).parent / "static" / "project_list.html"
    return FileResponse(html_path)


# Admin Dashboard Routes
@app.get("/admin", dependencies=[Depends(admin_only)], include_in_schema=False)
async def serve_admin_dashboard():
    """Serve the main admin dashboard"""
    html_path = Path(__file__).parent / "static" / "admin_projects.html"
    return FileResponse(html_path)

@app.get("/admin/dashboard", dependencies=[Depends(admin_only)], include_in_schema=False)
async def serve_admin_summary():
    """Serve the admin summary dashboard"""
    html_path = Path(__file__).parent / "static" / "admin_summary.html"
    return FileResponse(html_path)

@app.get("/admin/projects/new", dependencies=[Depends(admin_only)], include_in_schema=False)
async def serve_new_project_form():
    """Serve the new project creation form"""
    html_path = Path(__file__).parent / "static" / "new_project.html"
    return FileResponse(html_path)

@app.get("/admin/projects/{project_id}/edit", dependencies=[Depends(admin_only)], include_in_schema=False)
async def serve_edit_project_form(project_id: str):
    """Serve the project editing form"""
    html_path = Path(__file__).parent / "static" / "edit_project.html"
    return FileResponse(html_path)


#editProject
# Student Routes
@app.get("/projects/page", include_in_schema=False)
async def serve_projects_list():
    """Serve the projects list for students"""
    html_path = Path(__file__).parent / "static" / "project_list.html"
    return FileResponse(html_path)

@app.get("/student/form", include_in_schema=False)
async def serve_student_form():
    """Serve the student information form"""
    html_path = Path(__file__).parent / "static" / "student_form.html"
    return FileResponse(html_path)

@app.get("/submission/success", include_in_schema=False)
async def serve_submission_success():
    """Serve the submission success page"""
    html_path = Path(__file__).parent / "static" / "submission_success.html"
    return FileResponse(html_path)

@app.get("/admin/allocation", dependencies=[Depends(admin_only)], include_in_schema=False)
async def serve_admin_allocation():
    """Serve the admin allocation page"""
    html_path = Path(__file__).parent / "static" / "admin_allocation.html"
    return FileResponse(html_path)


# Admin endpoints for project management
@app.get("/admin/projects", dependencies=[Depends(admin_only)], include_in_schema=False)
async def get_admin_projects():
    """Get all projects for admin management"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            return []
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        return projects
    except Exception as e:
        print(f"Error loading projects for admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/projects/{project_id}", dependencies=[Depends(admin_only)], include_in_schema=False)
async def get_admin_project(project_id: str):
    """Get a specific project by ID for admin editing"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Projects file not found")
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        
        project = next((p for p in projects if p.get("id") == project_id), None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/projects/{project_id}", dependencies=[Depends(admin_only)], include_in_schema=False)
async def update_admin_project(project_id: str, project_data: dict = Body(...)):
    """Update a specific project by ID"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Projects file not found")
        
        # Load current projects
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        
        # Find and update the project
        project_index = next((i for i, p in enumerate(projects) if p.get("id") == project_id), None)
        if project_index is None:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update the project data
        projects[project_index].update(project_data)
        
        # Ensure the parent directory exists
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save updated projects
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "message": f"Project {project_id} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/projects/{project_id}", dependencies=[Depends(admin_only)], include_in_schema=False)
async def delete_admin_project(project_id: str):
    """Delete a specific project by ID"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Projects file not found")
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        
        original_count = len(projects)
        projects = [p for p in projects if p.get("id") != project_id]
        
        if len(projects) == original_count:
            raise HTTPException(status_code=404, detail="Project not found")
        
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "message": f"Project {project_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Additional API endpoints for enhanced functionality
@app.get("/api/stats", include_in_schema=False)
async def get_project_statistics():
    """Get project statistics for dashboard"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            return {"total_projects": 0, "total_skills": 0, "total_disciplines": 0}
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)

        all_skills = set()
        all_disciplines = set()
        
        for project in projects:
            if project.get("required_skills"):
                all_skills.update(project["required_skills"])
            if project.get("related_disciplines"):
                all_disciplines.update(project["related_disciplines"])
        
        return {
            "total_projects": len(projects),
            "total_skills": len(all_skills),
            "total_disciplines": len(all_disciplines),
            "avg_skills_per_project": round(len(all_skills) / len(projects), 2) if projects else 0
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills", include_in_schema=False)
async def get_all_skills():
    """Get all unique skills across all projects"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            return []
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        
        all_skills = set()
        for project in projects:
            if project.get("required_skills"):
                all_skills.update(project["required_skills"])
        
        return sorted(list(all_skills))
    except Exception as e:
        print(f"Error getting skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/disciplines", include_in_schema=False)
async def get_all_disciplines():
    """Get all unique disciplines across all projects"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            return []
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        
        all_disciplines = set()
        for project in projects:
            if project.get("related_disciplines"):
                all_disciplines.update(project["related_disciplines"])
        
        return sorted(list(all_disciplines))
    except Exception as e:
        print(f"Error getting disciplines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Student Application API endpoints
@app.post("/api/students", include_in_schema=False)
async def submit_student_application(group_data: dict = Body(...)):
    """Submit a group project selection application"""
    try:
        # Validate required fields
        required_fields = ["group_name", "students", "wam_distribution", "dual_enrollment", "suitability_description"]
        for field in required_fields:
            if not group_data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate group name format
        group_name = group_data.get("group_name")
        if not group_name or len(group_name.split('_')) != 3:
            raise HTTPException(status_code=400, detail="Group name must be in format: TutorialCode_TutorialDayTime_GroupNumber")
        
        # Validate students (5-7 students required)
        students = group_data.get("students", [])
        if len(students) < 5 or len(students) > 7:
            raise HTTPException(status_code=400, detail="Group must have 5-7 students")
        
        # Validate each student entry format
        for i, student in enumerate(students):
            if not student or len(student.split(',')) != 4:
                raise HTTPException(status_code=400, detail=f"Student {i+1} must be in format: name, student_id, unikey, UoS_code")
        
        
        # Validate WAM distribution
        wam_dist = group_data.get("wam_distribution", {})
        total_wam = wam_dist.get("hd", 0) + wam_dist.get("d", 0) + wam_dist.get("cr", 0) + wam_dist.get("p", 0)
        if total_wam != len(students):
            raise HTTPException(status_code=400, detail="WAM distribution must sum to the number of students in the group")
        
        # Validate dual enrollment
        dual_enrollment = group_data.get("dual_enrollment")
        if dual_enrollment not in ["Yes", "No"]:
            raise HTTPException(status_code=400, detail="Dual enrollment must be 'Yes' or 'No'")
        
        # Convert group data to individual student records
        student_records = []
        for i, student_info in enumerate(students):
            if student_info and student_info.strip():
                parts = student_info.split(',')
                if len(parts) == 4:
                    name, student_id, unikey, uos_code = [part.strip() for part in parts]
                    student_record = {
                        "name": name,
                        "student_id": student_id,
                        "unikey": unikey,
                        "unit_code": uos_code,
                        "wam": 0,  # Default WAM, will be calculated from distribution
                        "group_id": group_name,
                        "tutor_code": "T01",  # Default tutor
                        "dual_project_enrollment": dual_enrollment == "Yes",
                        "skills": group_data.get("skills", []),
                        "project_preferences": group_data.get("project_preferences", [])
                    }
                    student_records.append(student_record)
        
        # Calculate WAM for each student based on distribution
        wam_dist = group_data.get("wam_distribution", {})
        hd_count = wam_dist.get("hd", 0)
        d_count = wam_dist.get("d", 0)
        cr_count = wam_dist.get("cr", 0)
        p_count = wam_dist.get("p", 0)
        
        wam_index = 0
        for i in range(hd_count):
            if wam_index < len(student_records):
                student_records[wam_index]["wam"] = 87.5  # Mid-point of HD range
                wam_index += 1
        
        for i in range(d_count):
            if wam_index < len(student_records):
                student_records[wam_index]["wam"] = 80.0  # Mid-point of D range
                wam_index += 1
        
        for i in range(cr_count):
            if wam_index < len(student_records):
                student_records[wam_index]["wam"] = 70.0  # Mid-point of CR range
                wam_index += 1
        
        for i in range(p_count):
            if wam_index < len(student_records):
                student_records[wam_index]["wam"] = 57.5  # Mid-point of P range
                wam_index += 1
        
        # Load existing students or create new file
        students_path = Path(__file__).parent.parent / "data" / "students.json"
        students_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_students = []
        if students_path.exists():
            try:
                with open(students_path, "r", encoding="utf-8") as f:
                    existing_students = json.load(f)
            except json.JSONDecodeError:
                existing_students = []
        
        # Check if any student ID already exists
        existing_student_ids = {student.get("student_id") for student in existing_students}
        new_student_ids = {student["student_id"] for student in student_records}
        
        if existing_student_ids & new_student_ids:
            raise HTTPException(status_code=409, detail="One or more student IDs already exist")
        
        # Save student applications
        existing_students.extend(student_records)
        
        with open(students_path, "w", encoding="utf-8") as f:
            json.dump(existing_students, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "message": "Group application submitted successfully", "group_name": group_name}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting group application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students", include_in_schema=False)
async def get_student_applications():
    """Get all student applications (admin only)"""
    try:
        students_path = Path(__file__).parent.parent / "data" / "students.json"
        if not students_path.exists():
            return []
        
        with open(students_path, "r", encoding="utf-8") as f:
            students = json.load(f)
        
        return students
    except Exception as e:
        print(f"Error getting student applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/groups", include_in_schema=False)
async def get_group_applications():
    """Get all group applications (admin only)"""
    try:
        groups_path = Path(__file__).parent.parent / "data" / "groups.json"
        if not groups_path.exists():
            return []
        
        with open(groups_path, "r", encoding="utf-8") as f:
            groups = json.load(f)
        
        return groups
    except Exception as e:
        print(f"Error getting group applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# API endpoint for projects (used by frontend)
@app.get("/api/projects", include_in_schema=False)
async def get_api_projects():
    """Get all projects for API consumption"""
    try:
        json_path = Path(__file__).parent.parent / "data" / "projects.json"
        if not json_path.exists():
            return []
        
        with open(json_path, "r", encoding="utf-8") as f:
            projects = json.load(f)
        return projects
    except Exception as e:
        print(f"Error loading projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
@app.get("/projects", include_in_schema=False)
async def get_projects():
    """Get all projects (legacy endpoint)"""
    return await get_api_projects()
    
    
    
# Schedule Management API endpoints
@app.get("/api/schedule", include_in_schema=False)
async def get_allocation_schedule():
    """Get the current allocation schedule"""
    try:
        schedule_path = Path(__file__).parent.parent / "data" / "schedule.json"
        if not schedule_path.exists():
            return {
                "end_date": None
            }
        
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)
        return schedule
    except Exception as e:
        print(f"Error loading schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule", include_in_schema=False)
async def update_allocation_schedule(schedule_data: dict = Body(...)):
    """Update the allocation schedule"""
    try:
        # Validate required fields
        if "end_date" not in schedule_data:
            raise HTTPException(status_code=400, detail="Missing required field: end_date")
        
        # Validate date format
        try:
            from datetime import datetime
            if schedule_data["end_date"]:
                datetime.fromisoformat(schedule_data["end_date"].replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM)")
        
        # Save schedule
        schedule_path = Path(__file__).parent.parent / "data" / "schedule.json"
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(schedule_path, "w", encoding="utf-8") as f:
            json.dump(schedule_data, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "message": "Allocation deadline updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#update the projects
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
