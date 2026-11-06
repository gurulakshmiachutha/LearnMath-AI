
import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_NAME = "learnmate.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def connect_db():

    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# PASSWORD SECURITY
# ==========================================

def hash_password(password):

    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    ).hex()

    return salt + "$" + hashed


def check_password(password, saved_password):

    try:

        salt, old_hash = saved_password.split("$")

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            200000
        ).hex()

        return secrets.compare_digest(
            new_hash,
            old_hash
        )

    except Exception:

        return False


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            email TEXT PRIMARY KEY,
            otp_hash TEXT,
            expires_at TEXT,
            attempts INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            email TEXT,
            activity TEXT,
            details TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            email TEXT,
            subject TEXT,
            level TEXT,
            hours INTEGER,
            plan TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            email TEXT,
            subject TEXT,
            score INTEGER,
            total INTEGER,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tutor_interactions (
            email TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT
        )
    """)

    # Add missing columns without deleting existing records.
    required_columns = {
        "users": {
            "name": "TEXT",
            "email": "TEXT",
            "password_hash": "TEXT",
            "created_at": "TEXT"
        },
        "otp_codes": {
            "email": "TEXT",
            "otp_hash": "TEXT",
            "expires_at": "TEXT",
            "attempts": "INTEGER DEFAULT 0"
        },
        "activity_logs": {
            "email": "TEXT",
            "activity": "TEXT",
            "details": "TEXT",
            "created_at": "TEXT"
        },
        "study_plans": {
            "email": "TEXT",
            "subject": "TEXT",
            "level": "TEXT",
            "hours": "INTEGER",
            "plan": "TEXT",
            "created_at": "TEXT"
        },
        "quiz_results": {
            "email": "TEXT",
            "subject": "TEXT",
            "score": "INTEGER",
            "total": "INTEGER",
            "created_at": "TEXT"
        },
        "tutor_interactions": {
            "email": "TEXT",
            "question": "TEXT",
            "answer": "TEXT",
            "created_at": "TEXT"
        }
    }

    for table, columns in required_columns.items():

        cursor.execute(f"PRAGMA table_info({table})")

        existing = [
            row["name"]
            for row in cursor.fetchall()
        ]

        for column, data_type in columns.items():

            if column not in existing:

                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {data_type}"
                )

    connection.commit()
    connection.close()


# ==========================================
# USER REGISTRATION
# ==========================================

def user_exists(email):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT rowid
        FROM users
        WHERE lower(email) = lower(?)
    """, (email,))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def create_user(name, email, password):

    connection = connect_db()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email.lower(),
            hash_password(password),
            datetime.now().isoformat()
        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        connection.close()


# ==========================================
# USER LOGIN
# ==========================================

def login_user(email, password):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT rowid AS user_rowid,
               name,
               email,
               password_hash,
               created_at
        FROM users
        WHERE lower(email) = lower(?)
        ORDER BY rowid DESC
        LIMIT 1
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        return False

    user = dict(user)

    saved_password = user.get("password_hash")

    if not saved_password:
        return False

    if check_password(password, saved_password):

        user.pop("password_hash", None)

        return user

    return False


# ==========================================
# UPDATE PASSWORD
# ==========================================

def update_password(email, new_password):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE lower(email) = lower(?)
    """, (
        hash_password(new_password),
        email.lower()
    ))

    changed = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return changed


# ==========================================
# OTP FUNCTIONS
# ==========================================

def save_otp(email, otp_hash, expires_at):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO otp_codes
        (email, otp_hash, expires_at, attempts)
        VALUES (?, ?, ?, 0)
    """, (
        email.lower(),
        otp_hash,
        expires_at
    ))

    connection.commit()
    connection.close()


def get_otp(email):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM otp_codes
        WHERE lower(email) = lower(?)
    """, (email,))

    result = cursor.fetchone()

    connection.close()

    if result:
        return dict(result)

    return None


def increase_otp_attempts(email):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE otp_codes
        SET attempts = COALESCE(attempts, 0) + 1
        WHERE lower(email) = lower(?)
    """, (email,))

    connection.commit()
    connection.close()


def delete_otp(email):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM otp_codes
        WHERE lower(email) = lower(?)
    """, (email,))

    connection.commit()
    connection.close()


# ==========================================
# ACTIVITY TRACKING
# ==========================================

def log_activity(email, activity, details=""):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO activity_logs
        (email, activity, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        email.lower(),
        activity,
        details,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


# ==========================================
# STUDY PLAN RECORDS
# ==========================================

def save_study_plan(email, subject, level, hours, plan):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO study_plans
        (email, subject, level, hours, plan, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email.lower(),
        subject,
        level,
        hours,
        plan,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


# ==========================================
# QUIZ RECORDS
# ==========================================

def save_quiz_result(email, subject, score, total):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO quiz_results
        (email, subject, score, total, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        email.lower(),
        subject,
        score,
        total,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


# ==========================================
# AI TUTOR RECORDS
# ==========================================

def save_tutor_interaction(email, question, answer):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO tutor_interactions
        (email, question, answer, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        email.lower(),
        question,
        answer,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


# ==========================================
# REGISTERED STUDENTS
# ==========================================

def get_all_users():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            name,
            email,
            created_at
        FROM users
        ORDER BY rowid DESC
    """)

    result = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return result


# ==========================================
# STUDENT RECORDS
# ==========================================

def get_user_records(table, email):

    allowed_tables = [
        "activity_logs",
        "study_plans",
        "quiz_results",
        "tutor_interactions"
    ]

    if table not in allowed_tables:
        return []

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT rowid AS record_number, *
        FROM {table}
        WHERE lower(email) = lower(?)
        ORDER BY rowid DESC
        """,
        (email,)
    )

    result = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return result


# ==========================================
# ALL STUDENT RECORDS
# ==========================================

def get_all_records(table):

    allowed_tables = [
        "activity_logs",
        "study_plans",
        "quiz_results",
        "tutor_interactions"
    ]

    if table not in allowed_tables:
        return []

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT rowid AS record_number, *
        FROM {table}
        ORDER BY rowid DESC
        """
    )

    result = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return result


# ==========================================
# TOTAL STUDENTS
# ==========================================

def get_user_count():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    count = cursor.fetchone()[0]

    connection.close()

    return count


# Initialize database when imported.
init_db()
