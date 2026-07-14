import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'students.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS departments (
            dept_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name VARCHAR(100) NOT NULL,
            hod_name  VARCHAR(100),
            total_students INT DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name       VARCHAR(100) NOT NULL,
            roll_no    VARCHAR(20)  UNIQUE NOT NULL,
            dept_id    INTEGER      REFERENCES departments(dept_id),
            semester   INTEGER      NOT NULL,
            dob        DATE,
            email      VARCHAR(100) UNIQUE
        );

        CREATE TABLE IF NOT EXISTS subjects (
            subject_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name VARCHAR(100) NOT NULL,
            dept_id      INTEGER REFERENCES departments(dept_id),
            credits      INTEGER DEFAULT 4,
            semester     INTEGER
        );

        CREATE TABLE IF NOT EXISTS performance (
            perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER REFERENCES students(student_id),
            subject_id      INTEGER REFERENCES subjects(subject_id),
            marks_obtained  REAL,
            attendance_pct  REAL,
            semester        INTEGER,
            exam_year       INTEGER,
            assignment_rate REAL DEFAULT 75,
            study_hours     REAL DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS ai_predictions (
            pred_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id       INTEGER REFERENCES students(student_id),
            predicted_grade  VARCHAR(5),
            confidence       REAL,
            pass_probability REAL,
            model_version    VARCHAR(20),
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS risk_flags (
            flag_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(student_id),
            risk_level VARCHAR(20),
            factor     VARCHAR(200),
            flagged_on DATE,
            resolved   INTEGER DEFAULT 0,
            UNIQUE(student_id, risk_level)
        );
    ''')

    # Seed departments
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        departments = [
            ('Computer Science', 'Dr. Meera Joshi', 320),
            ('Electronics & Communication', 'Dr. Rajiv Patil', 280),
            ('Mechanical Engineering', 'Dr. Sunita Rao', 250),
            ('Information Technology', 'Dr. Arun Desai', 298),
            ('Civil Engineering', 'Dr. Priya Kulkarni', 200),
        ]
        cursor.executemany("INSERT INTO departments (dept_name, hod_name, total_students) VALUES (?,?,?)", departments)

        subjects = [
            ('Mathematics', 1, 4, 1), ('Data Structures', 1, 4, 2), ('Database Systems', 1, 4, 3),
            ('Machine Learning', 1, 4, 4), ('Computer Networks', 1, 4, 5), ('Operating Systems', 1, 4, 3),
            ('Physics', 2, 4, 1), ('Circuit Theory', 2, 4, 2), ('Digital Electronics', 2, 4, 3),
            ('Signal Processing', 2, 4, 4), ('Engineering Drawing', 3, 4, 1), ('Thermodynamics', 3, 4, 2),
            ('Web Technologies', 4, 4, 3), ('Software Engineering', 4, 4, 4), ('English Communication', 1, 2, 1),
        ]
        cursor.executemany("INSERT INTO subjects (subject_name, dept_id, credits, semester) VALUES (?,?,?,?)", subjects)

        students = [
            ('Aarav Rao',       'CS2201', 1, 4, '2004-03-12', 'aarav.rao@college.edu'),
            ('Priya Sharma',    'EC2105', 2, 3, '2005-07-22', 'priya.sharma@college.edu'),
            ('Rohan Kumar',     'ME2308', 3, 5, '2003-11-05', 'rohan.kumar@college.edu'),
            ('Ananya Nair',     'CS2204', 1, 4, '2004-01-30', 'ananya.nair@college.edu'),
            ('Vikram Gupta',    'IT2302', 4, 6, '2002-08-18', 'vikram.gupta@college.edu'),
            ('Sneha Patil',     'CS2206', 1, 3, '2005-04-14', 'sneha.patil@college.edu'),
            ('Arjun Mehta',     'EC2208', 2, 5, '2003-09-25', 'arjun.mehta@college.edu'),
            ('Kavya Reddy',     'IT2310', 4, 4, '2004-06-08', 'kavya.reddy@college.edu'),
            ('Ravi Deshmukh',   'ME2312', 3, 3, '2005-02-17', 'ravi.deshmukh@college.edu'),
            ('Ishaan Verma',    'CS2214', 1, 6, '2002-12-03', 'ishaan.verma@college.edu'),
            ('Pooja Kulkarni',  'EC2116', 2, 4, '2004-10-21', 'pooja.kulkarni@college.edu'),
            ('Nikhil Joshi',    'IT2318', 4, 5, '2003-05-29', 'nikhil.joshi@college.edu'),
            ('Tanvi Singh',     'CS2220', 1, 2, '2006-03-11', 'tanvi.singh@college.edu'),
            ('Rahul Bhat',      'ME2320', 3, 4, '2004-07-19', 'rahul.bhat@college.edu'),
            ('Meera Iyer',      'CS2222', 1, 5, '2003-01-26', 'meera.iyer@college.edu'),
        ]
        cursor.executemany("INSERT INTO students (name, roll_no, dept_id, semester, dob, email) VALUES (?,?,?,?,?,?)", students)

        import random
        random.seed(42)
        performances = []
        for sid in range(1, 16):
            base = random.randint(45, 95)
            for subj in random.sample(range(1, 16), 5):
                marks = min(100, max(20, base + random.randint(-15, 15)))
                att   = min(100, max(40, base + random.randint(-20, 10)))
                asgn  = min(100, max(40, base + random.randint(-15, 10)))
                hrs   = round(random.uniform(4, 22), 1)
                performances.append((sid, subj, marks, att, random.randint(2, 6), 2024, asgn, hrs))
        cursor.executemany('''
            INSERT INTO performance (student_id, subject_id, marks_obtained, attendance_pct,
                                     semester, exam_year, assignment_rate, study_hours)
            VALUES (?,?,?,?,?,?,?,?)
        ''', performances)

        # Seed some predictions
        from models.predictor import predict_grade
        for sid in range(1, 16):
            cursor.execute('''
                SELECT AVG(marks_obtained), AVG(attendance_pct), AVG(assignment_rate), AVG(study_hours)
                FROM performance WHERE student_id = ?
            ''', (sid,))
            row = cursor.fetchone()
            if row[0]:
                f = {'prev_gpa': round(row[0]/25, 2), 'attendance': row[1], 'assignment_rate': row[2], 'study_hours': row[3]}
                r = predict_grade(f)
                cursor.execute('''
                    INSERT INTO ai_predictions (student_id, predicted_grade, confidence, pass_probability, model_version)
                    VALUES (?,?,?,?,'1.0')
                ''', (sid, r['grade'], r['confidence'], r['pass_probability']))
                if r['risk_level'] in ('high', 'critical'):
                    cursor.execute('''
                        INSERT OR IGNORE INTO risk_flags (student_id, risk_level, factor, flagged_on, resolved)
                        VALUES (?,?,?,DATE('now'),0)
                    ''', (sid, r['risk_level'], r['main_factor']))

    conn.commit()
    conn.close()
    print("✅ Database initialised at", DB_PATH)
