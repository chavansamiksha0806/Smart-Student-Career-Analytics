from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
from io import BytesIO

from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)
app.secret_key = "smart_student_career_secret_key"

DATABASE = "database/student.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required():
    return "user_id" in session


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:

            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO student_profiles (user_id)
                VALUES (?)
            """, (user_id,))

            cursor.execute("""
                INSERT INTO student_progress (user_id)
                VALUES (?)
            """, (user_id,))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    progress = connection.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    skills = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()

    # =====================================================
    # PROFILE COMPLETION
    # =====================================================

    profile_fields = [
        profile["college"],
        profile["course"],
        profile["year"],
        profile["cgpa"],
        profile["skills"],
        profile["certifications"],
        profile["projects"],
        profile["internship"]
    ]

    completed_fields = sum(
        1 for field in profile_fields
        if field not in (None, "")
    )

    profile_completion = int(
        (completed_fields / len(profile_fields)) * 100
    )


    # =====================================================
    # BASIC COUNTS
    # =====================================================

    skill_count = len(skills)

    if profile["projects"]:
        project_count = len([
            project.strip()
            for project in profile["projects"].split(",")
            if project.strip()
        ])
    else:
        project_count = 0


    # =====================================================
    # PREPARATION SCORE
    # =====================================================

    preparation_score = 0

    # CGPA - maximum 20 points
    cgpa = profile["cgpa"] or 0

    if cgpa >= 9:
        preparation_score += 20
    elif cgpa >= 8:
        preparation_score += 17
    elif cgpa >= 7:
        preparation_score += 14
    elif cgpa >= 6:
        preparation_score += 10
    else:
        preparation_score += 5


    # Skills - maximum 15 points
    skill_score = min(skill_count * 2, 15)
    preparation_score += skill_score


    # Projects - maximum 15 points
    preparation_score += min(project_count * 5, 15)


    # Certifications - maximum 5 points
    if profile["certifications"]:
        certification_count = len([
            item.strip()
            for item in profile["certifications"].split(",")
            if item.strip()
        ])

        preparation_score += min(certification_count, 5)


    # Internship - maximum 10 points
    if profile["internship"]:
        internship_value = profile["internship"].lower()

        if internship_value not in ["no", "none", ""]:
            preparation_score += 10


    # Progress score
    if progress:

        # Coding - maximum 10
        coding_score = min(
            (progress["coding_problems"] / 100) * 10,
            10
        )

        preparation_score += coding_score


        # SQL - maximum 5
        sql_score = min(
            (progress["sql_problems"] / 50) * 5,
            5
        )

        preparation_score += sql_score


        # Aptitude - maximum 10
        aptitude_score = min(
            progress["aptitude_score"] / 100 * 10,
            10
        )

        preparation_score += aptitude_score


        # Communication - maximum 5
        communication_score = min(
            progress["communication_score"] / 100 * 5,
            5
        )

        preparation_score += communication_score


        # Mock Interviews - maximum 5
        mock_score = min(
            progress["mock_interviews"] / 5 * 5,
            5
        )

        preparation_score += mock_score


    preparation_score = round(
        min(preparation_score, 100)
    )


    # =====================================================
    # READINESS LEVEL
    # =====================================================

    if preparation_score >= 80:
        readiness_level = "Placement Ready"

    elif preparation_score >= 60:
        readiness_level = "Developing"

    else:
        readiness_level = "Needs Improvement"


    # =====================================================
    # SKILLS PREVIEW
    # =====================================================

    skills_preview = skills[:6]


    # =====================================================
    # DYNAMIC RECOMMENDATIONS
    # =====================================================

    recommendations = []

    required_skills = [
        "Python",
        "SQL",
        "DSA",
        "Git",
        "GitHub",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask",
        "DBMS",
        "OOP"
    ]


    skill_map = {
        skill["skill_name"].lower(): skill["skill_level"]
        for skill in skills
    }


    # -----------------------------------------------------
    # SKILL-BASED RECOMMENDATIONS
    # -----------------------------------------------------

    for skill in required_skills:

        level = skill_map.get(skill.lower())


        # Missing skill
        if level is None:

            recommendations.append({
                "title": f"Learn {skill}",
                "description": (
                    f"{skill} is currently missing "
                    "from your skill profile."
                ),
                "link": url_for("skills")
            })


        # Very weak skill
        elif level < 50:

            recommendations.append({
                "title": f"Improve {skill}",
                "description": (
                    f"Your current {skill} level is "
                    f"{level}%. Give this skill higher priority."
                ),
                "link": url_for("skills")
            })


        # Needs practice
        elif level < 75:

            recommendations.append({
                "title": f"Practice {skill}",
                "description": (
                    f"Your {skill} level is {level}%. "
                    "More practice will strengthen it."
                ),
                "link": url_for("skills")
            })


    # -----------------------------------------------------
    # PROGRESS-BASED RECOMMENDATIONS
    # -----------------------------------------------------

    if progress:

        # Coding
        if progress["coding_problems"] < 100:

            recommendations.append({
                "title": "Practice DSA",
                "description": (
                    f"You have solved "
                    f"{progress['coding_problems']} coding problems. "
                    "Target 100+ problems."
                ),
                "link": url_for("progress")
            })


        # SQL
        if progress["sql_problems"] < 50:

            recommendations.append({
                "title": "Improve SQL",
                "description": (
                    f"You have solved "
                    f"{progress['sql_problems']} SQL problems. "
                    "Target 50+ problems."
                ),
                "link": url_for("progress")
            })


        # Aptitude
        if progress["aptitude_score"] < 75:

            recommendations.append({
                "title": "Improve Aptitude",
                "description": (
                    f"Your aptitude score is "
                    f"{progress['aptitude_score']}%. "
                    "Practice regularly."
                ),
                "link": url_for("progress")
            })


        # Communication
        if progress["communication_score"] < 75:

            recommendations.append({
                "title": "Improve Communication",
                "description": (
                    f"Your communication score is "
                    f"{progress['communication_score']}%. "
                    "Practice interview communication."
                ),
                "link": url_for("progress")
            })


        # Mock interviews
        if progress["mock_interviews"] < 5:

            recommendations.append({
                "title": "Prepare for Interviews",
                "description": (
                    f"You have completed "
                    f"{progress['mock_interviews']} mock interviews. "
                    "Target at least 5."
                ),
                "link": url_for("progress")
            })


    # Only show first 4
    recommendations = recommendations[:4]


    # =====================================================
    # RENDER DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",
        profile=profile,
        progress=progress,
        skills=skills,
        profile_completion=profile_completion,
        skill_count=skill_count,
        project_count=project_count,
        preparation_score=preparation_score,
        readiness_level=readiness_level,
        skills_preview=skills_preview,
        recommendations=recommendations
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    if request.method == "POST":

        college = request.form["college"]
        course = request.form["course"]
        year = request.form["year"]
        cgpa = request.form["cgpa"]
        skills = request.form["skills"]
        certifications = request.form["certifications"]
        projects = request.form["projects"]
        internship = request.form["internship"]

        connection.execute("""
            UPDATE student_profiles
            SET
                college = ?,
                course = ?,
                year = ?,
                cgpa = ?,
                skills = ?,
                certifications = ?,
                projects = ?,
                internship = ?
            WHERE user_id = ?
        """, (
            college,
            course,
            year,
            cgpa,
            skills,
            certifications,
            projects,
            internship,
            user_id
        ))

        connection.commit()

        connection.close()

        return redirect(url_for("profile"))


    profile_data = connection.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    connection.close()

    return render_template(
        "profile.html",
        profile=profile_data
    )


# =========================================================
# PROGRESS
# =========================================================

@app.route("/progress", methods=["GET", "POST"])
def progress():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    if request.method == "POST":

        coding_problems = request.form["coding_problems"]
        sql_problems = request.form["sql_problems"]
        aptitude_score = request.form["aptitude_score"]
        communication_score = request.form["communication_score"]
        mock_interviews = request.form["mock_interviews"]

        connection.execute("""
            UPDATE student_progress
            SET
                coding_problems = ?,
                sql_problems = ?,
                aptitude_score = ?,
                communication_score = ?,
                mock_interviews = ?
            WHERE user_id = ?
        """, (
            coding_problems,
            sql_problems,
            aptitude_score,
            communication_score,
            mock_interviews,
            user_id
        ))

        connection.commit()


    progress_data = connection.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    connection.close()


    coding_percentage = min(
        int((progress_data["coding_problems"] / 100) * 100),
        100
    )

    sql_percentage = min(
        int((progress_data["sql_problems"] / 50) * 100),
        100
    )

    aptitude_percentage = min(
        int(progress_data["aptitude_score"]),
        100
    )

    communication_percentage = min(
        int(progress_data["communication_score"]),
        100
    )


    return render_template(
        "progress.html",
        progress=progress_data,
        coding_percentage=coding_percentage,
        sql_percentage=sql_percentage,
        aptitude_percentage=aptitude_percentage,
        communication_percentage=communication_percentage
    )


# =========================================================
# SKILLS
# =========================================================

@app.route("/skills", methods=["GET", "POST"])
def skills():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    if request.method == "POST":

        skill_name = request.form["skill_name"]
        skill_level = request.form["skill_level"]

        connection.execute("""
            INSERT INTO student_skills
            (
                user_id,
                skill_name,
                skill_level
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            skill_name,
            skill_level
        ))

        connection.commit()


    skills_data = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()


    return render_template(
        "skills.html",
        skills=skills_data
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
def analytics():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    progress = connection.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    skills_data = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()


    # =====================================================
    # PREPARATION SCORE
    # =====================================================

    preparation_score = 0

    cgpa = profile["cgpa"] or 0

    if cgpa >= 9:
        preparation_score += 20
    elif cgpa >= 8:
        preparation_score += 17
    elif cgpa >= 7:
        preparation_score += 14
    elif cgpa >= 6:
        preparation_score += 10
    else:
        preparation_score += 5


    preparation_score += min(
        len(skills_data) * 2,
        15
    )


    if profile["projects"]:

        project_count = len([
            p.strip()
            for p in profile["projects"].split(",")
            if p.strip()
        ])

    else:

        project_count = 0


    preparation_score += min(
        project_count * 5,
        15
    )


    if profile["certifications"]:

        certification_count = len([
            c.strip()
            for c in profile["certifications"].split(",")
            if c.strip()
        ])

        preparation_score += min(
            certification_count,
            5
        )


    if profile["internship"]:

        internship_value = profile["internship"].lower()

        if internship_value not in ["no", "none", ""]:
            preparation_score += 10


    preparation_score += min(
        (progress["coding_problems"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["sql_problems"] / 50) * 5,
        5
    )

    preparation_score += min(
        (progress["aptitude_score"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["communication_score"] / 100) * 5,
        5
    )

    preparation_score += min(
        (progress["mock_interviews"] / 5) * 5,
        5
    )


    preparation_score = round(
        min(preparation_score, 100)
    )


    if preparation_score >= 80:
        readiness_level = "Placement Ready"

    elif preparation_score >= 60:
        readiness_level = "Developing"

    else:
        readiness_level = "Needs Improvement"


    # =====================================================
    # PROFILE COMPLETION
    # =====================================================

    profile_fields = [
        profile["college"],
        profile["course"],
        profile["year"],
        profile["cgpa"],
        profile["skills"],
        profile["certifications"],
        profile["projects"],
        profile["internship"]
    ]

    completed_fields = sum(
        1 for field in profile_fields
        if field not in (None, "")
    )

    profile_completion = int(
        completed_fields / len(profile_fields) * 100
    )


    # =====================================================
    # TECHNICAL SKILLS DATA
    # =====================================================

    technical_skills_progress = []

    for skill in skills_data:

        technical_skills_progress.append({
            "name": skill["skill_name"],
            "level": skill["skill_level"]
        })


    # =====================================================
    # PROJECT PROGRESS
    # =====================================================

    projects_progress = project_count


    # =====================================================
    # OTHER PROGRESS
    # =====================================================

    coding_percentage = min(
        int(progress["coding_problems"]),
        100
    )

    sql_percentage = min(
        int(progress["sql_problems"] * 2),
        100
    )

    aptitude_score = progress["aptitude_score"]

    communication_score = progress["communication_score"]


    return render_template(
        "analytics.html",
        profile=profile,
        progress=progress,
        skills=skills_data,
        placement_score=preparation_score,
        readiness_level=readiness_level,
        profile_completion=profile_completion,
        technical_skills_progress=technical_skills_progress,
        projects_progress=projects_progress,
        coding_percentage=coding_percentage,
        sql_percentage=sql_percentage,
        aptitude_score=aptitude_score,
        communication_score=communication_score
    )


# =========================================================
# SKILL GAP ANALYSIS
# =========================================================

@app.route("/skill-gap")
def skill_gap():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    skills_data = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()


    # =====================================================
    # REQUIRED PLACEMENT SKILLS
    # =====================================================

    required_skills = [
        "Python",
        "SQL",
        "DSA",
        "Git",
        "GitHub",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask",
        "DBMS",
        "OOP"
    ]


    # =====================================================
    # LEARNING RESOURCES
    # =====================================================

    learning_resources = {

        "Python":
            "Practice Python programming, functions, OOP and problem solving.",

        "SQL":
            "Practice SQL queries, joins, subqueries, grouping and database problems.",

        "DSA":
            "Practice arrays, strings, searching, sorting, stacks, queues and basic algorithms.",

        "Git":
            "Learn Git commands such as add, commit, push, pull, branch and merge.",

        "GitHub":
            "Practice repositories, README files, commits, branches and project documentation.",

        "HTML":
            "Build semantic and accessible web pages using HTML5.",

        "CSS":
            "Practice layouts, Flexbox, Grid, responsive design and modern styling.",

        "JavaScript":
            "Learn variables, functions, DOM manipulation, events and API integration.",

        "Flask":
            "Build Flask routes, templates, forms, sessions and database applications.",

        "DBMS":
            "Study normalization, keys, transactions, indexing and database concepts.",

        "OOP":
            "Practice classes, objects, inheritance, encapsulation and polymorphism."
    }


    # =====================================================
    # SKILL CATEGORIES
    # =====================================================

    strong_skills = []
    practice_skills = []
    priority_skills = []
    missing_skills = []


    existing_skill_names = []


    for skill in skills_data:

        skill_name = skill["skill_name"]
        skill_level = skill["skill_level"]

        existing_skill_names.append(
            skill_name.lower()
        )


        if skill_level >= 75:

            strong_skills.append(skill)


        elif skill_level >= 50:

            practice_skills.append(skill)


        else:

            priority_skills.append(skill)


    # =====================================================
    # FIND MISSING SKILLS
    # =====================================================

    for required_skill in required_skills:

        if required_skill.lower() not in existing_skill_names:

            missing_skills.append({
                "skill_name": required_skill
            })


    # =====================================================
    # PERSONALIZED LEARNING PLAN
    # =====================================================

    learning_plan = []


    # Practice skills
    for skill in practice_skills:

        skill_name = skill["skill_name"]

        learning_plan.append({
            "skill": skill_name,
            "level": skill["skill_level"],
            "resource": learning_resources.get(
                skill_name,
                f"Practice {skill_name} regularly."
            ),
            "priority": "Medium"
        })


    # Priority skills
    for skill in priority_skills:

        skill_name = skill["skill_name"]

        learning_plan.append({
            "skill": skill_name,
            "level": skill["skill_level"],
            "resource": learning_resources.get(
                skill_name,
                f"Focus on improving {skill_name}."
            ),
            "priority": "High"
        })


    # Missing skills
    for skill in missing_skills:

        skill_name = skill["skill_name"]

        learning_plan.append({
            "skill": skill_name,
            "level": 0,
            "resource": learning_resources.get(
                skill_name,
                f"Start learning {skill_name}."
            ),
            "priority": "High"
        })


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    recommendations = []


    if missing_skills:

        recommendations.append(
            "Start learning the missing placement skills."
        )


    if priority_skills:

        recommendations.append(
            "Give high priority to skills below 50%."
        )


    if practice_skills:

        recommendations.append(
            "Continue practicing skills between 50% and 74%."
        )


    if strong_skills:

        recommendations.append(
            "Maintain your strong skills through projects and practice."
        )


    if not recommendations:

        recommendations.append(
            "Continue improving your technical skills and interview preparation."
        )


    return render_template(
        "skill_gap.html",
        skills=skills_data,
        strong_skills=strong_skills,
        practice_skills=practice_skills,
        priority_skills=priority_skills,
        missing_skills=missing_skills,
        learning_plan=learning_plan,
        recommendations=recommendations
    )


# =========================================================
# CAREER REPORT
# =========================================================

@app.route("/report")
def report():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    progress = connection.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    skills_data = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()


    # =====================================================
    # SCORE
    # =====================================================

    preparation_score = 0


    cgpa = profile["cgpa"] or 0

    if cgpa >= 9:
        preparation_score += 20

    elif cgpa >= 8:
        preparation_score += 17

    elif cgpa >= 7:
        preparation_score += 14

    elif cgpa >= 6:
        preparation_score += 10

    else:
        preparation_score += 5


    preparation_score += min(
        len(skills_data) * 2,
        15
    )


    if profile["projects"]:

        project_count = len([
            p.strip()
            for p in profile["projects"].split(",")
            if p.strip()
        ])

    else:

        project_count = 0


    preparation_score += min(
        project_count * 5,
        15
    )


    if profile["certifications"]:

        certification_count = len([
            c.strip()
            for c in profile["certifications"].split(",")
            if c.strip()
        ])

        preparation_score += min(
            certification_count,
            5
        )


    if profile["internship"]:

        if profile["internship"].lower() not in [
            "no",
            "none",
            ""
        ]:

            preparation_score += 10


    preparation_score += min(
        (progress["coding_problems"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["sql_problems"] / 50) * 5,
        5
    )

    preparation_score += min(
        (progress["aptitude_score"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["communication_score"] / 100) * 5,
        5
    )

    preparation_score += min(
        (progress["mock_interviews"] / 5) * 5,
        5
    )


    preparation_score = round(
        min(preparation_score, 100)
    )


    # =====================================================
    # READINESS
    # =====================================================

    if preparation_score >= 80:

        readiness_level = "Placement Ready"

    elif preparation_score >= 60:

        readiness_level = "Developing"

    else:

        readiness_level = "Needs Improvement"


    return render_template(
        "report.html",
        profile=profile,
        progress=progress,
        skills=skills_data,
        preparation_score=preparation_score,
        readiness_level=readiness_level
    )


# =========================================================
# DOWNLOAD PDF CAREER REPORT
# =========================================================

@app.route("/download-report")
def download_report():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    progress = connection.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    skills_data = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE user_id = ?
        ORDER BY skill_level DESC
    """, (user_id,)).fetchall()

    connection.close()


    # =====================================================
    # CALCULATE SCORE
    # =====================================================

    preparation_score = 0


    cgpa = profile["cgpa"] or 0

    if cgpa >= 9:
        preparation_score += 20

    elif cgpa >= 8:
        preparation_score += 17

    elif cgpa >= 7:
        preparation_score += 14

    elif cgpa >= 6:
        preparation_score += 10

    else:
        preparation_score += 5


    preparation_score += min(
        len(skills_data) * 2,
        15
    )


    if profile["projects"]:

        project_count = len([
            p.strip()
            for p in profile["projects"].split(",")
            if p.strip()
        ])

    else:

        project_count = 0


    preparation_score += min(
        project_count * 5,
        15
    )


    if profile["certifications"]:

        certification_count = len([
            c.strip()
            for c in profile["certifications"].split(",")
            if c.strip()
        ])

        preparation_score += min(
            certification_count,
            5
        )


    if profile["internship"]:

        if profile["internship"].lower() not in [
            "no",
            "none",
            ""
        ]:

            preparation_score += 10


    preparation_score += min(
        (progress["coding_problems"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["sql_problems"] / 50) * 5,
        5
    )

    preparation_score += min(
        (progress["aptitude_score"] / 100) * 10,
        10
    )

    preparation_score += min(
        (progress["communication_score"] / 100) * 5,
        5
    )

    preparation_score += min(
        (progress["mock_interviews"] / 5) * 5,
        5
    )


    preparation_score = round(
        min(preparation_score, 100)
    )


    if preparation_score >= 80:

        readiness_level = "Placement Ready"

    elif preparation_score >= 60:

        readiness_level = "Developing"

    else:

        readiness_level = "Needs Improvement"


    # =====================================================
    # CREATE PDF
    # =====================================================

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )


    styles = getSampleStyleSheet()

    story = []


    # Title
    story.append(
        Paragraph(
            "Smart Student Career & Placement Analytics",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 15))


    story.append(
        Paragraph(
            f"Student: {session['user_name']}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 8))


    # =====================================================
    # PROFILE
    # =====================================================

    story.append(
        Paragraph(
            "Student Profile",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 8))


    profile_data = [
        ["College", profile["college"] or "-"],
        ["Course", profile["course"] or "-"],
        ["Year", profile["year"] or "-"],
        ["CGPA", str(profile["cgpa"] or "-")],
        ["Internship", profile["internship"] or "-"],
        ["Projects", profile["projects"] or "-"],
        ["Certifications", profile["certifications"] or "-"]
    ]


    profile_table = Table(
        profile_data,
        colWidths=[130, 350]
    )


    profile_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )


    story.append(profile_table)

    story.append(Spacer(1, 20))


    # =====================================================
    # SCORE
    # =====================================================

    story.append(
        Paragraph(
            "Preparation Score",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"{preparation_score}/100",
            styles["Heading1"]
        )
    )

    story.append(
        Paragraph(
            f"Preparation Level: {readiness_level}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))


    # =====================================================
    # PROGRESS
    # =====================================================

    story.append(
        Paragraph(
            "Preparation Progress",
            styles["Heading2"]
        )
    )

    progress_data = [
        ["Metric", "Value"],
        [
            "Coding Problems",
            str(progress["coding_problems"])
        ],
        [
            "SQL Problems",
            str(progress["sql_problems"])
        ],
        [
            "Aptitude Score",
            f"{progress['aptitude_score']}%"
        ],
        [
            "Communication Score",
            f"{progress['communication_score']}%"
        ],
        [
            "Mock Interviews",
            str(progress["mock_interviews"])
        ]
    ]


    progress_table = Table(
        progress_data,
        colWidths=[250, 230]
    )


    progress_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )


    story.append(progress_table)

    story.append(Spacer(1, 20))


    # =====================================================
    # TECHNICAL SKILLS
    # =====================================================

    story.append(
        Paragraph(
            "Technical Skills",
            styles["Heading2"]
        )
    )


    skills_table_data = [
        ["Skill", "Level"]
    ]


    for skill in skills_data:

        skills_table_data.append([
            skill["skill_name"],
            f"{skill['skill_level']}%"
        ])


    skills_table = Table(
        skills_table_data,
        colWidths=[250, 230]
    )


    skills_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )


    story.append(skills_table)

    story.append(Spacer(1, 20))


    # =====================================================
    # DISCLAIMER
    # =====================================================

    story.append(
        Paragraph(
            "<b>Note:</b> The preparation score is a "
            "project-defined learning and preparation "
            "indicator. It is not a prediction of actual "
            "placement probability.",
            styles["Normal"]
        )
    )


    # Build PDF
    document.build(story)

    buffer.seek(0)


    return send_file(
        buffer,
        as_attachment=True,
        download_name="career_report.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)