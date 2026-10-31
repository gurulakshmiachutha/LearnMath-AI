
import sqlite3

DB_NAME = "learnmate.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            course TEXT,
            subject TEXT,
            level TEXT,
            study_hours INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            subject TEXT,
            score INTEGER,
            total_questions INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tutor_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            subject TEXT,
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            subject TEXT,
            plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safely add missing columns to existing tables.
    cursor.execute("PRAGMA table_info(study_plans)")
    plan_columns = [row["name"] for row in cursor.fetchall()]

    if "plan" not in plan_columns:
        cursor.execute(
            "ALTER TABLE study_plans ADD COLUMN plan TEXT"
        )

    cursor.execute("PRAGMA table_info(study_plans)")
    plan_columns = [row["name"] for row in cursor.fetchall()]

    conn.commit()
    conn.close()


def save_student(name, email, subject, level, study_hours):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM students WHERE email = ?",
        (email,)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE students
            SET name = ?, subject = ?, level = ?, study_hours = ?
            WHERE email = ?
        """, (name, subject, level, study_hours, email))
    else:
        cursor.execute("""
            INSERT INTO students
            (name, email, subject, level, study_hours)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, subject, level, study_hours))

    conn.commit()
    conn.close()


def get_student(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE email = ?",
        (email,)
    )

    student = cursor.fetchone()
    conn.close()

    return student


def save_quiz_result(email, subject, score, total):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_results
        (student_email, subject, score, total_questions)
        VALUES (?, ?, ?, ?)
    """, (email, subject, score, total))

    conn.commit()
    conn.close()


def get_quiz_results(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM quiz_results
        WHERE student_email = ?
        ORDER BY id DESC
    """, (email,))

    results = cursor.fetchall()
    conn.close()

    return results


def save_tutor_question(email, subject, question, answer):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tutor_questions
        (student_email, subject, question, answer)
        VALUES (?, ?, ?, ?)
    """, (email, subject, question, answer))

    conn.commit()
    conn.close()


def get_tutor_questions(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM tutor_questions
        WHERE student_email = ?
        ORDER BY id DESC
    """, (email,))

    questions = cursor.fetchall()
    conn.close()

    return questions


def save_study_plan(email, subject, plan):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(study_plans)")
    columns = [row["name"] for row in cursor.fetchall()]

    # Support older database column names.
    if "plan" in columns:
        plan_column = "plan"
    elif "study_plan" in columns:
        plan_column = "study_plan"
    elif "content" in columns:
        plan_column = "content"
    else:
        conn.close()
        raise Exception("No supported study plan column found.")

    cursor.execute(
        f"""
        INSERT INTO study_plans
        (student_email, subject, {plan_column})
        VALUES (?, ?, ?)
        """,
        (email, subject, plan)
    )

    conn.commit()
    conn.close()


def get_latest_study_plan(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(study_plans)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "plan" in columns:
        plan_column = "plan"
    elif "study_plan" in columns:
        plan_column = "study_plan"
    elif "content" in columns:
        plan_column = "content"
    else:
        conn.close()
        return None

    cursor.execute(
        f"""
        SELECT * FROM study_plans
        WHERE student_email = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[plan_column]

    return None


def update_task_status(task_id, completed):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            completed INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        UPDATE tasks
        SET completed = ?
        WHERE id = ?
    """, (int(completed), task_id))

    conn.commit()
    conn.close()


init_db()
