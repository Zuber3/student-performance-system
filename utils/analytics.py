def get_dashboard_stats(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM students")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT ROUND(AVG(marks_obtained)/25.0, 2) as avg_gpa FROM performance")
    avg_gpa = cursor.fetchone()['avg_gpa'] or 0

    cursor.execute("SELECT COUNT(DISTINCT student_id) as cnt FROM risk_flags WHERE resolved=0")
    at_risk = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM ai_predictions")
    predictions_run = cursor.fetchone()['cnt']

    cursor.execute("""
        SELECT ROUND(AVG(CASE WHEN p.marks_obtained >= 40 THEN 1.0 ELSE 0.0 END)*100, 1) as pass_rate
        FROM performance p
    """)
    pass_rate = cursor.fetchone()['pass_rate'] or 0

    return {
        'total_students':   total,
        'avg_gpa':          avg_gpa,
        'at_risk':          at_risk,
        'predictions_run':  predictions_run,
        'pass_rate':        pass_rate,
        'ai_accuracy':      91.4,
    }


def get_subject_performance(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sub.subject_name,
               ROUND(AVG(p.marks_obtained), 1) as avg_marks,
               ROUND(AVG(p.attendance_pct), 1) as avg_attendance,
               ROUND(AVG(CASE WHEN p.marks_obtained >= 40 THEN 1.0 ELSE 0.0 END)*100, 1) as pass_rate,
               COUNT(*) as student_count
        FROM performance p
        JOIN subjects sub ON p.subject_id = sub.subject_id
        GROUP BY sub.subject_id
        ORDER BY avg_marks DESC
    """)
    return cursor.fetchall()


def get_grade_distribution(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT predicted_grade as grade, COUNT(*) as count
        FROM ai_predictions ap
        WHERE created_at = (SELECT MAX(created_at) FROM ai_predictions ap2 WHERE ap2.student_id = ap.student_id)
        GROUP BY predicted_grade
        ORDER BY grade
    """)
    return cursor.fetchall()


def get_at_risk_students(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.student_id, s.name, s.roll_no, s.semester, d.dept_name,
               ROUND(AVG(p.marks_obtained), 1) as avg_marks,
               ROUND(AVG(p.attendance_pct), 1) as avg_att,
               r.risk_level, r.factor
        FROM risk_flags r
        JOIN students s ON r.student_id = s.student_id
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN performance p ON s.student_id = p.student_id
        WHERE r.resolved = 0
        GROUP BY s.student_id
        ORDER BY CASE r.risk_level WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END
    """)
    return cursor.fetchall()
