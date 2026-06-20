# Interview Pass

> A smart, structured hiring platform that bridges the gap between HR professionals and job seekers — built with Django, MySQL, and Tailwind CSS.

---

## Overview

Interview Pass streamlines the end-to-end recruitment workflow. HR managers post jobs with custom screening questions, and job seekers apply by answering those questions directly — giving recruiters meaningful signal before any interview takes place.

---

## Features

### HR Manager
- Post, edit, and delete job listings
- Define role-specific interview questions per job
- View all applicants per listing with their answers
- Accept or reject candidates from a dedicated applicant profile view
- Dashboard with real-time hiring stats (total jobs, applications, pending, accepted)

### Job Seeker
- Browse all available job listings with live search (AJAX)
- Apply to jobs by answering structured interview questions
- Track application status (Pending / Accepted / Rejected) in real time
- Manage personal profile including LinkedIn, GitHub, bio, and profile photo

### Platform
- Role-based access control (HR / Job Seeker)
- Email notification API via Gmail SMTP
- REST API endpoint: `GET /api/jobs/`
- Fully responsive UI (mobile, tablet, desktop)
- Secure: CSRF protection, bcrypt password hashing, SQL injection prevention

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django (Python) |
| Database | MySQL |
| Frontend | Tailwind CSS (CDN), Vanilla JS |
| Authentication | Custom session-based auth with bcrypt |
| Email API | Gmail SMTP |
| Deployment | AWS EC2 + Nginx + Gunicorn |
| Version Control | Git / GitHub |

---

## Architecture

```
interview_pass_project/
├── interview_pass_project/     # Django project settings & main URLs
├── login_app/                  # User auth: register, login, logout, profile
│   ├── models.py               # User model with UserManager (Fat Model pattern)
│   ├── views.py                # Skinny controllers
│   └── urls.py
├── interview_pass_app/         # Core app: jobs, applications, answers
│   ├── models.py               # Job, Question, Application, Answer, Skill
│   ├── views.py
│   └── urls.py
├── templates/
│   ├── hr/                     # HR-specific templates
│   ├── jobseeker/              # Job seeker templates
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   └── about.html
├── static/
│   └── js/main.js
└── media/                      # User-uploaded profile pictures
```

---

## Database Schema

```
User
├── id, first_name, last_name, email, password_hash
├── role (hr | jobseeker)
├── github_url, linkedin_url, resume (TextField)
├── profile_pic (ImageField)
└── created_at, updated_at

Job
├── id, title, description, experience_level
├── hr → FK(User)
├── skills → M2M(Skill)
└── created_at, updated_at

Skill
└── id, name (unique)

Question
├── id, question_text
├── job → FK(Job)
└── created_at, updated_at

Application
├── id, status (pending | accepted | rejected)
├── job_seeker → FK(User)
├── job → FK(Job)
└── applied_at, created_at, updated_at

Answer
├── id, answer_text
├── application → FK(Application)
├── question → FK(Question)
└── created_at, updated_at
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/interview-pass.git
cd interview-pass

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create MySQL database
mysql -u root -p
CREATE DATABASE job_portal_db;
EXIT;

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your MySQL credentials and email settings

# 6. Run migrations
python manage.py makemigrations
python manage.py migrate

# 7. Start development server
python manage.py runserver
```

---

## API

### `GET /api/jobs/`

Returns all available job listings.

**Response**
```json
[
  {
    "id": 1,
    "title": "Senior Frontend Developer",
    "description": "We are looking for...",
    "experience_level": "Senior",
    "skills": ["React", "TypeScript", "Redux"],
    "created_at": "2026-06-18"
  }
]
```

---
## AI Features (Google Gemini)

Interview Pass integrates **Google Gemini 2.5 Flash** to assist HR managers with three intelligent features:

### 1. Generate Job Description
Automatically generates a professional 3–4 paragraph job description based on the job title, required skills, and experience level.

**Used in:** Create Job page  
**Function:** `generate_description(title, skills, experience_level)`

### 2. Generate Interview Questions
Suggests 5 role-specific technical interview questions tailored to the job requirements.

**Used in:** Create Job page  
**Function:** `generate_questions(title, skills, experience_level)`

### 3. Analyze Candidate CV
Evaluates a candidate's resume against the job requirements and returns a structured analysis.

**Used in:** Applicant Profile page  
**Function:** `analyze_cv(resume_text, job)`

**Returns:**
```json
{
  "match_score": 85,
  "strengths": ["Strong React experience", "TypeScript proficiency"],
  "gaps": ["No Redux experience mentioned"],
  "summary": "Strong candidate with relevant frontend skills..."
}
```

### Setup

Add your Gemini API key to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Install the required package:

```bash
pip install google-genai python-dotenv
```

> The service includes automatic retry logic with exponential backoff on 503 errors (up to 3 attempts).

## Deployment

Deployed on **AWS EC2** (Ubuntu) using:
- **Gunicorn** as the WSGI server
- **Nginx** as the reverse proxy
- **MySQL** as the production database

```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn interview_pass_project.wsgi:application --bind 0.0.0.0:8000
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Fat Model / Skinny Controller | Business logic lives in Manager classes, keeping views clean and testable |
| Custom auth over Django's built-in | Full control over user fields and bcrypt hashing |
| ManyToMany for Skills | Proper normalization — skills are reusable entities, not raw strings |
| Client-side AJAX search | Avoids server round-trips for live job filtering; simpler and faster for the current dataset size |
| Session-based auth | Simpler than JWT for a server-rendered Django app |

---

## Author

**Sara Ayash**  
Full Stack Developer — AXSOS Academy (Python Stack)  
---

## License

This project was built as a solo capstone project at AXSOS Academy. All rights reserved.ِ