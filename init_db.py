import sqlite3

DATABASE = "database/student.db"

# Connect to database
connection = sqlite3.connect(DATABASE)

cursor = connection.cursor()


# ==================================================
# 1. USERS TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# ==================================================
# 2. STUDENT PROFILES TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    college TEXT,
    course TEXT,
    year TEXT,
    cgpa REAL,
    skills TEXT,
    certifications TEXT,
    projects TEXT,
    internship TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# ==================================================
# 3. STUDENT PROGRESS TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,

    coding_problems INTEGER DEFAULT 0,

    sql_problems INTEGER DEFAULT 0,

    aptitude_score REAL DEFAULT 0,

    communication_score REAL DEFAULT 0,

    mock_interviews INTEGER DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
# ==================================================
# 4. STUDENT SKILLS TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_skills (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    skill_name TEXT NOT NULL,

    skill_level INTEGER DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES users(id)

)
""")

# ==================================================
# SAVE CHANGES
# ==================================================

connection.commit()

connection.close()

print("Database created successfully!")