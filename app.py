from flask import Flask, render_template, request, jsonify, redirect, url_for
from database.db_setup import init_db, get_db_connection
from models.predictor import predict_grade
from utils.analytics import get_dashboard_stats, get_subject_performance,get_grade_distribution, get_at_risk_students
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    stats = get_dashboard_stats(conn)
    subjects = get_subject_performance(conn)
    grades = get_grade_distribution(conn)
    conn.close()
    return render_template('dashboard.html', stats=stats, subjects=subjects, grades=grades)

@app.route('/students')
def students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.student_id, s.name, s.roll_no, s.semester, s.email,
               d.dept_name,
               ROUND(AVG(p.marks_obtained), 2) as avg_marks,
               ROUND(AVG(p.attendance_pct), 1) as avg_attendance,
               r.risk_level
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN performance p ON s.student_id = p.student_id
        LEFT JOIN risk_flags r ON s.student_id = r.student_id AND r.resolved = 0
        GROUP BY s.student_id
        ORDER BY s.name
    ''') 
    students_list = cursor.fetchall()
    conn.close()
    return render_template('students.html', students=students_list)

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, d.dept_name FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        WHERE s.student_id = ?
    ''', (student_id,))
    student = cursor.fetchone()

    cursor.execute('''
        SELECT p.*, sub.subject_name FROM performance p
        JOIN subjects sub ON p.subject_id = sub.subject_id
        WHERE p.student_id = ?
        ORDER BY p.exam_year DESC, p.semester DESC
    ''', (student_id,))
    performances = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM ai_predictions WHERE student_id = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (student_id,))
    prediction = cursor.fetchone()

    cursor.execute('''
        SELECT * FROM risk_flags WHERE student_id = ? AND resolved = 0
    ''', (student_id,))
    risks = cursor.fetchall()

    conn.close()
    return render_template('student_detail.html', student=student,
                           performances=performances, prediction=prediction, risks=risks)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments')
    departments = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        dept_id = request.form['dept_id']
        semester = request.form['semester']
        dob = request.form['dob']
        email = request.form['email']
        cursor.execute('''
            INSERT INTO students (name, roll_no, dept_id, semester, dob, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, roll_no, dept_id, semester, dob, email))
        conn.commit()
        conn.close()
        return redirect(url_for('students'))

    conn.close()
    return render_template('add_student.html', departments=departments)

@app.route('/add_performance', methods=['GET', 'POST'])
def add_performance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, name, roll_no FROM students ORDER BY name')
    students_list = cursor.fetchall()
    cursor.execute('SELECT subject_id, subject_name FROM subjects ORDER BY subject_name')
    subjects_list = cursor.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        marks = request.form['marks_obtained']
        attendance = request.form['attendance_pct']
        semester = request.form['semester']
        year = request.form['exam_year']
        assignment_rate = request.form['assignment_rate']
        study_hours = request.form['study_hours']

        cursor.execute('''
            INSERT INTO performance (student_id, subject_id, marks_obtained, attendance_pct,
                                     semester, exam_year, assignment_rate, study_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, subject_id, marks, attendance, semester, year, assignment_rate, study_hours))

        # Auto-run prediction and risk check
        cursor.execute('''
            SELECT AVG(marks_obtained), AVG(attendance_pct), AVG(assignment_rate), AVG(study_hours)
            FROM performance WHERE student_id = ?
        ''', (student_id,))
        row = cursor.fetchone()
        if row[0]:
            features = {
                 'prev_gpa': round(row[0] / 25, 2),
                 'attendance': round(row[1], 1),
                 'assignment_rate': round(row[2], 1),
                 'study_hours': round(row[3], 1)
            }
            result = predict_grade(features)
            cursor.execute('''
                INSERT INTO ai_predictions (student_id, predicted_grade, confidence, pass_probability, model_version)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, result['grade'], result['confidence'], result['pass_probability'], '1.0'))

            # Risk flagging
            if result['risk_level'] in ('high', 'critical'):
                cursor.execute('''
                    INSERT OR REPLACE INTO risk_flags (student_id, risk_level, factor, flagged_on, resolved)
                    VALUES (?, ?, ?, DATE('now'), 0)
                ''', (student_id, result['risk_level'], result['main_factor']))

        conn.commit()
        conn.close()
        return redirect(url_for('students'))

    conn.close()
    return render_template('add_performance.html', students=students_list, subjects=subjects_list)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    result = None
    if request.method == 'POST':
        features = {
            'prev_gpa': float(request.form.get('percentage', 2.5)),
            'attendance': float(request.form.get('attendance', 75)),
            'assignment_rate': float(request.form.get('assignment_rate', 75)),
            'study_hours': float(request.form.get('study_hours', 10))
        }
        result = predict_grade(features)
    return render_template('predict.html', result=result)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    result = predict_grade(data)
    return jsonify(result)

@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    conn = get_db_connection()
    stats = get_dashboard_stats(conn)
    subjects = get_subject_performance(conn)
    grades = get_grade_distribution(conn)
    conn.close()
    return jsonify({'stats': dict(stats), 'subjects': [dict(s) for s in subjects], 'grades': [dict(g) for g in grades]})

@app.route('/at_risk')
def at_risk():
    conn = get_db_connection()
    students_at_risk = get_at_risk_students(conn)
    conn.close()
    return render_template('at_risk.html', students=students_at_risk)

@app.route('/database_schema')
def database_schema():
    return render_template('database_schema.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
