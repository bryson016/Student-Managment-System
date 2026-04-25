import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = 'database.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        # Users with role (admin/teacher/student)
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'student'
                    )''')
        # Students
        c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                    )''')
        # Courses
        c.execute('''CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    teacher_id INTEGER,
                    FOREIGN KEY (teacher_id) REFERENCES users (id)
                    )''')
        # Enrollments/Grades
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    grade REAL DEFAULT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                    )''')
        conn.commit()

        # Migration: Ensure role and email columns exist for existing DB
        c.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in c.fetchall()]
        if 'role' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
        if 'email' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()

        # Seed default courses
        seed_courses()

def seed_courses():
    default_courses = [
        'Data Networking',
        'Software Testing',
        'Data Structure and Algorithm',
        'Web Development',
        'Object-Oriented Programming (OOP)',
        'Operating System',
    ]
    with get_db() as conn:
        c = conn.cursor()
        for course_name in default_courses:
            try:
                c.execute("INSERT OR IGNORE INTO courses (name) VALUES (?)", (course_name,))
            except sqlite3.IntegrityError:
                pass
        conn.commit()

def get_user(username, password):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user and check_password_hash(user[2], password):
            return user
    return None

def create_user(username, email, password, role='student'):
    hashed = generate_password_hash(password)
    with get_db() as conn:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                      (username, email, hashed, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_all_students():
    with get_db() as conn:
        return conn.execute('SELECT * FROM students ORDER BY name').fetchall()

def get_student(student_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM students WHERE id=?', (student_id,))
        return c.fetchone()

def create_student(name, email):
    with get_db() as conn:
        try:
            conn.execute('INSERT INTO students (name, email) VALUES (?, ?)', (name, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def update_student(student_id, name, email):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('UPDATE students SET name=?, email=? WHERE id=?', (name, email, student_id))
        conn.commit()
        return c.rowcount > 0

def delete_student(student_id):
    with get_db() as conn:
        conn.execute('DELETE FROM students WHERE id=?', (student_id,))
        conn.commit()

def get_all_courses():
    with get_db() as conn:
        return conn.execute('SELECT * FROM courses ORDER BY name').fetchall()

def create_course(name, teacher_id=None):
    with get_db() as conn:
        try:
            conn.execute('INSERT INTO courses (name, teacher_id) VALUES (?, ?)', (name, teacher_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_student_courses(student_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT c.*, e.grade 
            FROM enrollments e 
            JOIN courses c ON e.course_id = c.id 
            WHERE e.student_id = ?
        """, (student_id,))
        return c.fetchall()

def enroll_student(student_id, course_id, grade=None):
    with get_db() as conn:
        try:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO enrollments (student_id, course_id, grade) VALUES (?, ?, ?)", 
                      (student_id, course_id, grade))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
