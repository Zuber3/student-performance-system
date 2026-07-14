# Smart Student Performance Analysis System
## DBMS + Artificial Intelligence Project

A full-stack web application built with **Python (Flask)**, **SQLite (DBMS)**, and an **AI prediction engine** that analyses student performance and predicts academic outcomes.

---

## 📁 Project Structure

```
student_performance_system/
├── app.py                    # Main Flask application + all routes
├── requirements.txt          # Python dependencies
├── database/
│   ├── db_setup.py           # Schema creation + seed data
│   └── students.db           # SQLite database (auto-created on first run)
├── models/
│   └── predictor.py          # AI grade prediction engine
├── utils/
│   └── analytics.py          # SQL analytics helper functions
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html            # Home page
│   ├── dashboard.html        # Analytics dashboard
│   ├── students.html         # Student roster
│   ├── student_detail.html   # Individual student profile
│   ├── predict.html          # AI predictor form
│   ├── at_risk.html          # At-risk student list
│   ├── add_student.html      # Add student form
│   └── add_performance.html  # Add marks form
└── static/
    └── css/
        └── style.css         # Full stylesheet
```

---

## ⚙️ Setup & Run

### 1. Install Python 3.8+
Make sure Python 3 is installed: `python --version`

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

The database (`students.db`) is **auto-created** with 15 sample students, 5 departments, 15 subjects, and seeded performance data on first run.

---

## 🗄️ Database Schema (SQLite)

| Table | Description |
|---|---|
| `departments` | Faculty departments (CS, EC, ME, IT, Civil) |
| `students` | Student records with roll number, dept, semester |
| `subjects` | Subjects per department |
| `performance` | Marks, attendance, assignments per subject per student |
| `ai_predictions` | AI-generated grade predictions with confidence |
| `risk_flags` | Auto-generated early warning flags |

---

## 🤖 AI Prediction Algorithm

**Weighted feature scoring (mimics Random Forest ensemble):**

```
score = (GPA/4.0) × 0.38  +  (Attendance/100) × 0.28
      + (Assignments/100) × 0.20  +  (StudyHrs/20) × 0.14
```

| Score Range | Grade | Risk Level |
|---|---|---|
| ≥ 0.88 | A | None |
| 0.78–0.88 | A- | None |
| 0.70–0.78 | B+ | None |
| 0.62–0.70 | B | Low |
| 0.54–0.62 | C+ | Low |
| 0.46–0.54 | C | Medium |
| 0.38–0.46 | D | High |
| < 0.38 | F | Critical |

**To use a real sklearn model:**
Replace the `predict_grade()` function in `models/predictor.py` with joblib model loading (commented code is already provided in that file).

---

## 🌐 Pages & Routes

| Route | Page |
|---|---|
| `/` | Home — project overview |
| `/dashboard` | Analytics with charts |
| `/students` | Full student roster with search |
| `/student/<id>` | Individual student profile + radar chart |
| `/predict` | AI grade predictor form |
| `/at_risk` | At-risk student list |
| `/add_student` | Add new student |
| `/add_performance` | Add marks (auto-triggers AI prediction) |
| `/api/predict` | JSON API endpoint for predictions |

---

## 📚 Technologies Used

- **Backend**: Python 3, Flask
- **Database**: SQLite3 (built-in Python module)
- **AI/ML**: Weighted feature scoring (production-ready sklearn swap-in)
- **Frontend**: HTML5, CSS3, Jinja2 templates
- **Charts**: Chart.js 4.4
- **Fonts**: Inter (Google Fonts)
