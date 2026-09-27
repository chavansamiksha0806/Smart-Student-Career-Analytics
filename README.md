# 🎓 Smart Student Career & Placement Analytics

A Flask-based web application designed to help students track their academic performance, technical skills, coding progress, interview preparation, and career development in one place.

The system provides **skill gap analysis, preparation tracking, analytics, personalized recommendations, and PDF career reports** through an easy-to-use dashboard.

---

## 📌 Project Overview

Students often use different platforms to track their coding practice, skills, certifications, projects, aptitude preparation, and interview progress.

**Smart Student Career & Placement Analytics** brings these activities together into a single web application.

The application allows students to:

* Create and manage their student profile
* Track technical skills and skill levels
* Monitor coding and SQL practice
* Track aptitude and communication performance
* Record mock interviews
* Analyze placement-related skill gaps
* Receive personalized learning recommendations
* View preparation analytics
* Generate a career preparation report
* Download a PDF report

> **Note:** The preparation score in this project is a project-defined progress indicator. It is not a prediction of actual placement probability.

---

## ✨ Key Features

### 👤 Student Registration & Login

* Student registration
* Secure password hashing
* Login and logout functionality
* Session-based authentication

### 📝 Student Profile

Students can maintain:

* Name
* Email
* College
* Course
* Academic year
* CGPA
* Technical skills
* Certifications
* Projects
* Internship status

### 📊 Career Dashboard

The dashboard provides an overview of the student's preparation:

* Profile completion
* Number of skills
* Number of projects
* Preparation score
* Preparation level
* Technical skill overview
* Career focus
* Personalized recommendations
* Quick navigation to important sections

### 📈 Progress Tracking

Students can track:

* Coding problems solved
* SQL problems solved
* Aptitude score
* Communication score
* Mock interviews completed

### 🧠 Skill Management

Students can add and track individual technical skills with a percentage-based skill level.

Example:

| Skill  | Level |
| ------ | ----: |
| Python |  100% |
| HTML   |  100% |
| SQL    |   75% |
| Flask  |   75% |
| CSS    |   75% |
| DSA    |   50% |
| Git    |   50% |

### 🔍 Skill Gap Analysis

The application compares the student's recorded skills with a predefined set of placement-oriented skills.

The system identifies:

* 🟢 Strong Skills
* 🟡 Skills Needing Practice
* 🔴 Priority Skills
* ⚠️ Missing Skills

Current placement skill set includes:

```text
Python
SQL
DSA
Git
GitHub
HTML
CSS
JavaScript
Flask
DBMS
OOP
```

### 🎯 Personalized Learning Plan

Based on the student's skill levels, the application generates recommendations such as:

* Learn a missing skill
* Improve a low-level skill
* Practice an intermediate skill
* Improve DSA
* Improve SQL
* Practice aptitude
* Improve communication
* Prepare for mock interviews

### 📊 Analytics

The analytics section provides a visual overview of the student's preparation and development.

### 📄 Career Report

Students can view a consolidated career preparation report containing information about:

* Academic profile
* Technical skills
* Coding progress
* SQL progress
* Aptitude
* Communication
* Mock interviews
* Preparation status

### 📥 PDF Report

The application can generate and download a PDF career preparation report.

---

## 🛠️ Technologies Used

### Frontend

* HTML5
* CSS3
* Jinja2 Templates

### Backend

* Python
* Flask

### Database

* SQLite

### Libraries

* Werkzeug
* ReportLab

### Development Tools

* Git
* GitHub
* Visual Studio Code / Code Editor
* Python Virtual Environment

---

## 🏗️ Project Architecture

```text
Smart-Student-Career-Analytics
│
├── app.py
├── init_db.py
├── requirements.txt
├── .gitignore
│
├── database/
│   └── db.py
│
├── templates/
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── profile.html
│   ├── dashboard.html
│   ├── progress.html
│   ├── analytics.html
│   ├── skills.html
│   ├── skill_gap.html
│   └── report.html
│
└── static/
    └── css/
        └── style.css
```

---

## 🔄 Application Workflow

```text
                    ┌─────────────────────┐
                    │       Student       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Register / Login    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Student Profile   │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ┌──────────┐   ┌──────────┐   ┌──────────┐
          │  Skills  │   │ Progress │   │ Profile  │
          └────┬─────┘   └────┬─────┘   └──────────┘
               │              │
               └───────┬──────┘
                       ▼
              ┌─
```
