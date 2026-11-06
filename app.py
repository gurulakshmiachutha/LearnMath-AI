
import os
import re
import json
import hmac
import hashlib
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from google import genai

import database as db
from gemini_helper import generate_ai_response

# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

st.set_page_config(
    page_title="LearnMate AI",
    page_icon="🎓",
    layout="wide"
)

db.init_db()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
OTP_HASH_SECRET = os.getenv("OTP_HASH_SECRET", "change-this-secret")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


SUBJECTS = [
    "Mathematics",
    "Engineering Mathematics",
    "Discrete Mathematics",
    "Physics",
    "Chemistry",
    "Computer Science",
    "Python Programming",
    "Java Programming",
    "C Programming",
    "C++ Programming",
    "Data Structures and Algorithms",
    "DBMS",
    "Operating Systems",
    "Computer Networks",
    "Software Engineering",
    "Artificial Intelligence",
    "Machine Learning",
    "Web Development",
    "Computer Organization and Architecture",
    "Digital Logic Design",
    "English",
    "Aptitude and Logical Reasoning",
    "Environmental Science",
    "Other"
]


# ==================================================
# SESSION STATE
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "register_otp_sent" not in st.session_state:
    st.session_state.register_otp_sent = False

if "forgot_otp_sent" not in st.session_state:
    st.session_state.forgot_otp_sent = False


# ==================================================
# COMMON FUNCTIONS
# ==================================================

def normalize_email(email):
    return email.strip().lower()


def record_activity(activity, details=""):

    if st.session_state.user:
        db.log_activity(
            st.session_state.user["email"],
            activity,
            details
        )


def is_admin():

    if not st.session_state.user:
        return False

    return (
        normalize_email(st.session_state.user["email"])
        == ADMIN_EMAIL
        and ADMIN_EMAIL != ""
    )


def otp_hash(otp):

    return hmac.new(
        OTP_HASH_SECRET.encode(),
        otp.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_otp_hash(otp, saved_hash):

    return hmac.compare_digest(
        otp_hash(otp),
        str(saved_hash)
    )


# ==================================================
# EMAIL OTP
# ==================================================

def send_otp_email(email, otp):

    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        raise ValueError("Gmail configuration is missing in .env.")

    message = EmailMessage()
    message["Subject"] = "LearnMate AI - Verification OTP"
    message["From"] = SMTP_EMAIL
    message["To"] = email

    message.set_content(
        f"""
Welcome to LearnMate AI.

Your OTP is {otp}

This OTP expires in 10 minutes.

Do not share this OTP with anyone.
"""
    )

    if SMTP_PORT == 465:

        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            context=ssl.create_default_context(),
            timeout=20
        ) as server:

            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(message)

    else:

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(message)


def create_and_send_otp(email):

    otp = str(secrets.randbelow(900000) + 100000)

    expiry = (
        datetime.now() + timedelta(minutes=10)
    ).isoformat()

    send_otp_email(email, otp)

    db.save_otp(
        normalize_email(email),
        otp_hash(otp),
        expiry
    )


def check_otp(email, entered_otp):

    saved = db.get_otp(normalize_email(email))

    if not saved:
        return False, "OTP not found. Request a new OTP."

    if int(saved.get("attempts", 0)) >= 5:
        db.delete_otp(email)
        return False, "Too many attempts. Request a new OTP."

    try:
        expiry = datetime.fromisoformat(saved["expires_at"])

        if datetime.now() > expiry:
            db.delete_otp(email)
            return False, "OTP expired. Request a new OTP."

    except Exception:
        return False, "Invalid OTP expiry information."

    if not verify_otp_hash(entered_otp.strip(), saved["otp_hash"]):
        db.increase_otp_attempts(email)
        return False, "Incorrect OTP."

    return True, "OTP verified successfully."


# ==================================================
# GEMINI AI
# ==================================================

def generate_gemini_response(prompt):

    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is missing in .env.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text


def show_ai_error(error):

    message = str(error)

    if "429" in message or "RESOURCE_EXHAUSTED" in message:

        st.warning(
            "Gemini API quota is exhausted. "
            "The offline learning system will be used."
        )

    elif "404" in message or "NOT_FOUND" in message:

        st.error(
            "Gemini model was not found. Check GEMINI_MODEL in .env."
        )

    elif "API_KEY_INVALID" in message or "API key not valid" in message:

        st.error("Gemini API key is invalid. Check your .env file.")

    else:

        st.error("Gemini error: " + message)


def test_gemini():

    try:

        answer = generate_gemini_response(
            "Reply with exactly: Gemini connection successful."
        )

        return True, answer

    except Exception as error:

        return False, str(error)


# ==================================================
# OFFLINE STUDY PLAN
# ==================================================

def offline_plan(subject, level, hours, goal):

    topics = {

        "Python Programming": [
            "Python basics and variables",
            "Data types and operators",
            "Conditional statements",
            "Loops",
            "Lists and dictionaries",
            "Functions and modules",
            "Practice and revision"
        ],

        "Java Programming": [
            "Java fundamentals",
            "Variables and data types",
            "Conditions and loops",
            "Classes and objects",
            "Inheritance and polymorphism",
            "Exception handling",
            "Practice and revision"
        ],

        "C Programming": [
            "C fundamentals",
            "Variables and operators",
            "Conditional statements",
            "Loops",
            "Arrays and strings",
            "Functions and pointers",
            "Practice and revision"
        ],

        "Data Structures and Algorithms": [
            "Algorithm analysis",
            "Arrays and strings",
            "Stacks",
            "Queues",
            "Linked lists",
            "Trees and graphs",
            "Searching and sorting"
        ],

        "DBMS": [
            "DBMS introduction",
            "ER diagrams",
            "Relational model",
            "SQL commands",
            "Joins and subqueries",
            "Normalization",
            "Transactions and revision"
        ],

        "Operating Systems": [
            "OS fundamentals",
            "Process management",
            "CPU scheduling",
            "Threads and synchronization",
            "Deadlocks",
            "Memory management",
            "File systems"
        ],

        "Computer Networks": [
            "Network fundamentals",
            "OSI model",
            "TCP/IP model",
            "Data link layer",
            "IP addressing",
            "Transport layer",
            "Application layer"
        ],

        "Artificial Intelligence": [
            "AI introduction",
            "Intelligent agents",
            "Search algorithms",
            "Knowledge representation",
            "Machine learning basics",
            "AI applications",
            "Revision"
        ],

        "Machine Learning": [
            "ML introduction",
            "Supervised learning",
            "Unsupervised learning",
            "Regression",
            "Classification",
            "Model evaluation",
            "Revision"
        ],

        "Web Development": [
            "HTML",
            "CSS",
            "JavaScript",
            "DOM",
            "Responsive design",
            "Forms and validation",
            "Mini project"
        ]
    }

    selected_topics = topics.get(
        subject,
        [
            f"Introduction to {subject}",
            f"Basic concepts of {subject}",
            f"Important definitions of {subject}",
            f"Core topics in {subject}",
            f"Examples and applications of {subject}",
            f"Practice questions in {subject}",
            f"Revision of {subject}"
        ]
    )

    plan = f"""
# 7-Day Study Plan

Subject: {subject}

Level: {level}

Daily hours: {hours}

Goal: {goal}

"""

    for day in range(7):

        plan += f"""
## Day {day + 1}

Topic: {selected_topics[day]}

Study activities:

1. Read and understand the topic.
2. Prepare short notes.
3. Practise examples.
4. Solve questions.
5. Revise the topic.

Daily study time: {hours} hours.

"""

    return plan


def generate_plan(subject, level, hours, goal):

    prompt = f"""
You are an expert college teacher.

Create a detailed 7-day study plan.

Subject: {subject}
Level: {level}
Daily hours: {hours}
Goal: {goal}

For every day include:
1. Topic
2. Explanation
3. Practical activity
4. Practice questions
5. Revision task

Use simple language suitable for a BTech student.
"""

    try:

        return generate_gemini_response(prompt), "Gemini AI"

    except Exception as error:

        show_ai_error(error)

        return offline_plan(subject, level, hours, goal), "Offline Study Planner"


# ==================================================
# OFFLINE TUTOR
# ==================================================

def offline_tutor(subject, question):

    q = question.lower()

    topics = {

        "Python Programming": {
            "variable": "A variable stores a value. Example: age = 20.",
            "loop": "Loops repeat statements. Python supports for and while loops.",
            "list": "A list stores multiple values. Example: numbers = [10, 20, 30].",
            "function": "A function is a reusable block of code defined using def.",
            "dictionary": "A dictionary stores key-value pairs.",
            "inheritance": "Inheritance allows one class to reuse another class's properties and methods.",
            "if": "An if statement executes code when a condition is true.",
            "data type": "Common Python types include int, float, str, bool, list, tuple and dict."
        },

        "Java Programming": {
            "class": "A class is a blueprint for creating objects.",
            "object": "An object is an instance of a class.",
            "inheritance": "Inheritance allows a Java class to inherit another class using extends.",
            "polymorphism": "Polymorphism means one interface or method name can have different forms.",
            "constructor": "A constructor initializes an object and has the same name as its class."
        },

        "C Programming": {
            "pointer": "A pointer stores the memory address of another variable.",
            "array": "An array stores multiple values of the same data type.",
            "loop": "C supports for, while and do-while loops.",
            "function": "A function is a reusable block of code.",
            "structure": "A structure groups different data types under one name."
        },

        "Data Structures and Algorithms": {
            "stack": "A stack follows LIFO: Last In, First Out. Operations include push, pop and peek.",
            "queue": "A queue follows FIFO: First In, First Out. Operations include enqueue and dequeue.",
            "linked list": "A linked list contains nodes connected using links.",
            "binary search": "Binary search searches sorted data by repeatedly dividing the search interval in half. Its time complexity is O(log n).",
            "sorting": "Sorting arranges elements. Examples include bubble sort, selection sort, insertion sort, merge sort and quick sort."
        },

        "DBMS": {
            "primary key": "A primary key uniquely identifies each record in a table.",
            "foreign key": "A foreign key refers to a key in another table and establishes a relationship.",
            "normalization": "Normalization organizes tables to reduce redundancy.",
            "sql": "SQL means Structured Query Language. SELECT retrieves records, INSERT adds records, UPDATE modifies records and DELETE removes records."
        },

        "Operating Systems": {
            "process": "A process is a program in execution.",
            "deadlock": "Deadlock occurs when processes wait indefinitely for resources held by one another.",
            "scheduling": "CPU scheduling selects which process gets the CPU. Algorithms include FCFS, SJF and Round Robin.",
            "memory": "Memory management allocates and manages main memory for processes."
        },

        "Computer Networks": {
            "osi": "The OSI model has seven layers: Physical, Data Link, Network, Transport, Session, Presentation and Application.",
            "tcp": "TCP is a reliable, connection-oriented transport protocol.",
            "ip address": "An IP address identifies a device on an IP network."
        },

        "Artificial Intelligence": {
            "agent": "An intelligent agent observes its environment and takes actions to achieve goals.",
            "machine learning": "Machine learning enables systems to learn patterns from data.",
            "search": "Search algorithms explore possible states to find a solution."
        },

        "Mathematics": {
            "matrix": "A matrix is a rectangular arrangement of values in rows and columns.",
            "derivative": "A derivative measures the rate of change of a function.",
            "integration": "Integration is used to find accumulated quantities and areas under curves."
        },

        "Physics": {
            "newton": "Newton's laws describe the relationship between force and motion.",
            "force": "Force is an interaction that can change an object's motion. F = ma.",
            "energy": "Energy is the capacity to do work."
        },

        "Chemistry": {
            "atom": "An atom is the basic unit of a chemical element.",
            "molecule": "A molecule consists of two or more atoms chemically bonded together.",
            "bond": "A chemical bond holds atoms together."
        }
    }

    selected = topics.get(subject, {})

    matches = []

    for keyword, answer in selected.items():

        if keyword in q:
            matches.append(answer)

    if matches:
        return "\n\n".join(matches)

    return (
        f"Your question is not covered by the offline {subject} topic library. "
        "Try asking about a basic definition, concept or example. "
        "Gemini AI is required for broader generated answers."
    )


def tutor_answer(subject, question, difficulty):

    prompt = f"""
You are LearnMate AI, a college subject tutor.

Subject: {subject}
Difficulty: {difficulty}
Question: {question}

Explain in simple language.

Include:
1. Definition
2. Explanation
3. Example
4. Important points
5. One practice question
"""

    try:

        return generate_gemini_response(prompt), "Gemini AI"

    except Exception as error:

        show_ai_error(error)

        return offline_tutor(subject, question), "Offline Tutor"


# ==================================================
# QUIZ
# ==================================================

QUIZ_BANK = {

    "Python Programming": [
        ("Which keyword defines a function?", ["function", "def", "fun", "define"], "def", "Python uses def to define functions."),
        ("Which type stores True or False?", ["int", "str", "bool", "list"], "bool", "bool represents True or False."),
        ("Which symbol starts a Python comment?", ["//", "#", "/*", "--"], "#", "Python uses # for comments."),
        ("Which collection is mutable?", ["tuple", "string", "list", "int"], "list", "Lists can be modified."),
        ("What does len() return?", ["Length", "Type", "Address", "Value"], "Length", "len() returns the number of items.")
    ],

    "Java Programming": [
        ("Which keyword creates an object?", ["class", "new", "this", "static"], "new", "new creates objects."),
        ("What is Java's entry point?", ["start()", "run()", "main()", "init()"], "main()", "Java execution begins in main()."),
        ("Which keyword supports class inheritance?", ["extends", "implements", "import", "package"], "extends", "extends is used for class inheritance."),
        ("Which type stores true or false?", ["int", "boolean", "char", "float"], "boolean", "boolean stores true or false."),
        ("Which symbol ends a Java statement?", [".", ":", ";", ","], ";", "Java statements generally end with semicolons.")
    ],

    "C Programming": [
        ("Which function displays output?", ["scanf", "printf", "main", "read"], "printf", "printf displays formatted output."),
        ("Which header contains printf?", ["stdlib.h", "string.h", "stdio.h", "math.h"], "stdio.h", "printf is declared in stdio.h."),
        ("Array indexing starts from?", ["1", "0", "-1", "2"], "0", "C array indexing starts from zero."),
        ("Which operator gives an address?", ["*", "&", "%", "#"], "&", "& is the address-of operator."),
        ("Which loop executes at least once?", ["for", "while", "do-while", "none"], "do-while", "do-while checks its condition after execution.")
    ],

    "Data Structures and Algorithms": [
        ("Which principle does a stack follow?", ["FIFO", "LIFO", "Random", "None"], "LIFO", "A stack follows Last In, First Out."),
        ("Which principle does a queue follow?", ["LIFO", "FIFO", "Random", "None"], "FIFO", "A queue follows First In, First Out."),
        ("Which structure uses connected nodes?", ["Array", "Linked list", "Integer", "String"], "Linked list", "A linked list consists of connected nodes."),
        ("Binary search requires?", ["Unsorted data", "Sorted data", "No data", "Duplicate data"], "Sorted data", "Binary search requires sorted data."),
        ("Merge sort time complexity?", ["O(n)", "O(n log n)", "O(n²)", "O(1)"], "O(n log n)", "Merge sort takes O(n log n) time.")
    ],

    "DBMS": [
        ("What does DBMS stand for?", ["Database Management System", "Data Backup System", "Digital Base System", "Database Memory System"], "Database Management System", "DBMS means Database Management System."),
        ("Which key uniquely identifies a row?", ["Foreign key", "Primary key", "Duplicate key", "None"], "Primary key", "A primary key uniquely identifies a row."),
        ("Which SQL command retrieves data?", ["INSERT", "DELETE", "SELECT", "UPDATE"], "SELECT", "SELECT retrieves data."),
        ("Which command modifies existing records?", ["UPDATE", "CREATE", "DROP", "SELECT"], "UPDATE", "UPDATE modifies existing rows."),
        ("Why is normalization used?", ["Increase duplication", "Reduce redundancy", "Delete tables", "Create passwords"], "Reduce redundancy", "Normalization reduces redundancy.")
    ]
}


def make_quiz(subject, difficulty):

    prompt = f"""
Create five multiple-choice questions for a BTech student.

Subject: {subject}
Difficulty: {difficulty}

Return only valid JSON:

[
 {{
 "question": "Question",
 "options": ["A", "B", "C", "D"],
 "answer": "Correct option",
 "explanation": "Explanation"
 }}
]
"""

    try:

        response = generate_gemini_response(prompt)

        cleaned = re.sub(
            r"```(?:json)?|```",
            "",
            response
        ).strip()

        questions = json.loads(cleaned)

        if not isinstance(questions, list) or not questions:
            raise ValueError("Invalid quiz response.")

        for question in questions:

            if not all(
                key in question
                for key in ["question", "options", "answer"]
            ):
                raise ValueError("Incomplete quiz question.")

            if len(question["options"]) < 2:
                raise ValueError("Invalid quiz options.")

        return questions[:5], "Gemini AI"

    except Exception as error:

        show_ai_error(error)

        questions = QUIZ_BANK.get(subject)

        if questions is None:

            questions = [
                (
                    f"What helps you learn {subject}?",
                    [
                        "Regular practice",
                        "Avoiding revision",
                        "Skipping examples",
                        "Ignoring concepts"
                    ],
                    "Regular practice",
                    "Regular practice improves understanding."
                ),
                (
                    "What should you do after studying a topic?",
                    [
                        "Revise and practise",
                        "Forget it",
                        "Skip exercises",
                        "Avoid questions"
                    ],
                    "Revise and practise",
                    "Revision improves retention."
                )
            ] * 2 + [
                (
                    f"What is important in {subject}?",
                    [
                        "Understanding concepts",
                        "Avoiding concepts",
                        "Skipping practice",
                        "Ignoring examples"
                    ],
                    "Understanding concepts",
                    "Conceptual understanding is important."
                )
            ]

        result = []

        for question, options, answer, explanation in questions:

            result.append({
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": explanation
            })

        return result, "Offline Quiz"


# ==================================================
# REGISTRATION
# ==================================================

def registration_page():

    st.title("📝 Student Registration")

    name = st.text_input("Full Name", key="reg_name")
    email = st.text_input("Gmail Address", key="reg_email")
    password = st.text_input(
        "Create Password",
        type="password",
        key="reg_password"
    )

    if st.button("Send Email OTP"):

        email = normalize_email(email)

        if not name.strip() or not email or not password:
            st.error("Fill in all fields.")

        elif not re.fullmatch(r"[^@\s]+@gmail\.com", email):
            st.error("Enter a valid Gmail address.")

        elif len(password) < 8:
            st.error("Password must have at least 8 characters.")

        elif db.user_exists(email):
            st.error("This email is already registered.")

        else:

            try:

                create_and_send_otp(email)

                st.session_state.register_email = email
                st.session_state.register_otp_sent = True

                st.success("OTP sent to your Gmail.")

            except Exception as error:

                st.error("Gmail sending failed: " + str(error))

    if st.session_state.register_otp_sent:

        st.divider()
        st.subheader("Verify Email")

        entered_otp = st.text_input(
            "Enter 6-digit OTP",
            max_chars=6
        )

        if st.button("Verify OTP and Register"):

            email = st.session_state.register_email

            success, message = check_otp(email, entered_otp)

            if not success:

                st.error(message)

            elif db.user_exists(email):

                st.error("This email is already registered.")

            else:

                created = db.create_user(
                    st.session_state.reg_name.strip(),
                    email,
                    st.session_state.reg_password
                )

                if created:

                    db.delete_otp(email)

                    db.log_activity(
                        email,
                        "Registration",
                        "Email verified and account created."
                    )

                    st.session_state.register_otp_sent = False
                    st.session_state.register_email = ""

                    st.success("Registration successful. Please log in.")

                else:

                    st.error("Registration failed.")


# ==================================================
# LOGIN AND FORGOT PASSWORD
# ==================================================

def login_page():

    st.title("🔐 Student Login")

    email = st.text_input("Email Address", key="login_email")

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    if st.button("Login", use_container_width=True):

        email = normalize_email(email)

        login_result = db.login_user(email, password)

        if login_result:

            # login_user returns a dictionary in this database.py.
            # This also supports an older Boolean return.
            if isinstance(login_result, dict):

                user = login_result

            else:

                user = None

                for student in db.get_all_users():

                    if normalize_email(student["email"]) == email:
                        user = student
                        break

                if user is None:
                    st.error("Student account details could not be loaded.")
                    return

            st.session_state.logged_in = True
            st.session_state.user = user

            db.log_activity(
                email,
                "Login",
                "Student logged in."
            )

            st.success("Login successful.")
            st.rerun()

        else:

            st.error("Invalid email or password.")

    st.divider()
    st.subheader("Forgot Password")

    forgot_email = st.text_input(
        "Registered Gmail",
        key="forgot_email"
    )

    if st.button("Send Password Reset OTP"):

        forgot_email = normalize_email(forgot_email)

        if not db.user_exists(forgot_email):

            st.error("Email is not registered.")

        else:

            try:

                create_and_send_otp(forgot_email)

                st.session_state.forgot_email = forgot_email
                st.session_state.forgot_otp_sent = True

                st.success("Password reset OTP sent.")

            except Exception as error:

                st.error("Email sending failed: " + str(error))

    if st.session_state.forgot_otp_sent:

        reset_otp = st.text_input(
            "Enter reset OTP",
            key="reset_otp"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="reset_password"
        )

        if st.button("Verify OTP and Reset Password"):

            email = st.session_state.forgot_email

            success, message = check_otp(email, reset_otp)

            if not success:

                st.error(message)

            elif len(new_password) < 8:

                st.error("Password must have at least 8 characters.")

            else:

                changed = db.update_password(
                    email,
                    new_password
                )

                if changed:

                    db.delete_otp(email)

                    db.log_activity(
                        email,
                        "Password Reset",
                        "Password changed through OTP."
                    )

                    st.session_state.forgot_otp_sent = False

                    st.success("Password reset successfully.")

                else:

                    st.error("Password update failed.")


# ==================================================
# DASHBOARD
# ==================================================

def dashboard_page():

    user = st.session_state.user

    st.title("🎓 LearnMate AI")

    st.subheader("Your Personal AI Learning Assistant")

    st.write("Welcome, **" + user["name"] + "**")

    col1, col2, col3 = st.columns(3)

    col1.metric("Available Subjects", len(SUBJECTS))
    col2.metric("Study Plan", "7 Days")
    col3.metric("Learning Tools", "3")

    st.divider()

    st.markdown("""
    ### Features

    - 📚 7-Day AI Study Plan
    - 🤖 Multi-subject AI Tutor
    - 📝 Diagnostic Quiz
    - 📊 Student Activity Tracking
    - 🔐 Password Management
    """)


# ==================================================
# STUDY PLAN PAGE
# ==================================================

def study_plan_page():

    st.title("📚 7-Day AI Study Plan")

    subject = st.selectbox("Select Subject", SUBJECTS)

    level = st.selectbox(
        "Your Level",
        ["Beginner", "Intermediate", "Advanced"]
    )

    hours = st.slider(
        "Daily Study Hours",
        1,
        10,
        2
    )

    goal = st.text_area(
        "Your Learning Goal",
        placeholder="Example: Prepare for semester examination."
    )

    if st.button("Generate 7-Day Study Plan"):

        with st.spinner("Generating your study plan..."):

            plan, source = generate_plan(
                subject,
                level,
                hours,
                goal
            )

        st.success("Generated using " + source)

        st.markdown(plan)

        db.save_study_plan(
            st.session_state.user["email"],
            subject,
            level,
            hours,
            plan
        )

        record_activity(
            "Study Plan Generated",
            f"{subject} - {source}"
        )

        st.download_button(
            "Download Study Plan",
            plan,
            "LearnMate_Study_Plan.txt",
            mime="text/plain"
        )


# ==================================================
# AI TUTOR PAGE
# ==================================================

def tutor_page():

    st.title("🤖 AI Tutor")

    subject = st.selectbox(
        "Select Subject",
        SUBJECTS,
        key="tutor_subject"
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Beginner", "Intermediate", "Advanced"]
    )

    question = st.text_area(
        "Ask your question",
        placeholder="Example: Explain Python inheritance with an example."
    )

    if st.button("Ask AI Tutor"):

        if not question.strip():

            st.warning("Enter your question.")

        else:

            with st.spinner("Preparing answer..."):

                answer, source = tutor_answer(
                    subject,
                    question,
                    difficulty
                )

            st.success("Answer source: " + source)

            st.markdown(answer)

            db.save_tutor_interaction(
                st.session_state.user["email"],
                question,
                answer
            )

            record_activity(
                "AI Tutor Used",
                subject + " - " + source
            )


# ==================================================
# DIAGNOSTIC QUIZ PAGE
# ==================================================

def quiz_page():

    st.title("📝 Diagnostic Quiz")

    subject = st.selectbox(
        "Select Subject",
        SUBJECTS,
        key="quiz_subject"
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Beginner", "Intermediate", "Advanced"]
    )

    if st.button("Generate Quiz"):

        with st.spinner("Preparing questions..."):

            questions, source = make_quiz(
                subject,
                difficulty
            )

        st.session_state.quiz_questions = questions
        st.session_state.quiz_subject_name = subject
        st.session_state.quiz_source = source
        st.session_state.quiz_submitted = False

        st.rerun()

    if "quiz_questions" in st.session_state:

        questions = st.session_state.quiz_questions

        st.info("Quiz source: " + st.session_state.quiz_source)

        if not st.session_state.quiz_submitted:

            with st.form("quiz_form"):

                answers = []

                for index, question in enumerate(questions):

                    st.markdown(
                        f"**Question {index + 1}: {question['question']}**"
                    )

                    answer = st.radio(
                        "Choose answer",
                        question["options"],
                        key=f"quiz_{index}"
                    )

                    answers.append(answer)

                    st.divider()

                submitted = st.form_submit_button("Submit Quiz")

            if submitted:

                score = 0

                for index, question in enumerate(questions):

                    if (
                        answers[index].strip().lower()
                        == question["answer"].strip().lower()
                    ):
                        score += 1

                st.session_state.quiz_score = score
                st.session_state.quiz_answers = answers
                st.session_state.quiz_submitted = True

                db.save_quiz_result(
                    st.session_state.user["email"],
                    st.session_state.quiz_subject_name,
                    score,
                    len(questions)
                )

                record_activity(
                    "Quiz Completed",
                    f"{st.session_state.quiz_subject_name}: {score}/{len(questions)}"
                )

                st.rerun()

        else:

            score = st.session_state.quiz_score

            st.subheader("Your Quiz Result")

            st.metric(
                "Score",
                f"{score}/{len(questions)}"
            )

            st.progress(score / len(questions))

            for index, question in enumerate(questions):

                st.markdown(
                    f"**Question {index + 1}: {question['question']}**"
                )

                st.write(
                    "Your answer: "
                    + st.session_state.quiz_answers[index]
                )

                st.write(
                    "Correct answer: "
                    + question["answer"]
                )

                st.caption(
                    question.get("explanation", "")
                )

                st.divider()

            if st.button("Take Another Quiz"):

                del st.session_state.quiz_questions
                st.session_state.quiz_submitted = False

                st.rerun()


# ==================================================
# MY ACTIVITY
# ==================================================

def my_activity_page():

    st.title("📊 My Activity")

    email = st.session_state.user["email"]

    tables = {
        "Activity Logs": "activity_logs",
        "Study Plans": "study_plans",
        "Quiz Results": "quiz_results",
        "Tutor Interactions": "tutor_interactions"
    }

    for title, table in tables.items():

        st.subheader(title)

        records = db.get_user_records(table, email)

        if records:

            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No records available.")


# ==================================================
# CHANGE PASSWORD
# ==================================================

def change_password_page():

    st.title("🔑 Change Password")

    old_password = st.text_input(
        "Current Password",
        type="password"
    )

    new_password = st.text_input(
        "New Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password"
    )

    if st.button("Update Password"):

        email = st.session_state.user["email"]

        valid_user = db.login_user(email, old_password)

        if not valid_user:

            st.error("Current password is incorrect.")

        elif len(new_password) < 8:

            st.error("New password must have at least 8 characters.")

        elif new_password != confirm_password:

            st.error("Passwords do not match.")

        else:

            if db.update_password(email, new_password):

                record_activity(
                    "Password Changed",
                    "Student changed password."
                )

                st.success("Password changed successfully.")

            else:

                st.error("Password update failed.")


# ==================================================
# ADMIN PAGES
# ==================================================

def registered_students_page():

    st.title("👥 Registered Students")

    users = db.get_all_users()

    if users:

        st.metric("Total Students", len(users))

        st.dataframe(
            pd.DataFrame(users),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No registered students.")


def student_learning_records_page():

    st.title("📚 Student Learning Records")

    users = db.get_all_users()

    if not users:

        st.info("No students found.")
        return

    selected_email = st.selectbox(
        "Select Student",
        [user["email"] for user in users]
    )

    for title, table in [
        ("Study Plans", "study_plans"),
        ("Quiz Results", "quiz_results"),
        ("Tutor Interactions", "tutor_interactions"),
        ("Activity Logs", "activity_logs")
    ]:

        st.subheader(title)

        records = db.get_user_records(
            table,
            selected_email
        )

        if records:

            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No records available.")


def all_student_activities_page():

    st.title("📈 All Student Activities")

    for title, table in [
        ("Activity Logs", "activity_logs"),
        ("Study Plans", "study_plans"),
        ("Quiz Results", "quiz_results"),
        ("Tutor Interactions", "tutor_interactions")
    ]:

        st.subheader(title)

        records = db.get_all_records(table)

        if records:

            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No records available.")


# ==================================================
# AUTHENTICATION
# ==================================================

def authentication_page():

    st.title("🎓 LearnMate AI")

    st.subheader("Your Personal AI Learning Assistant")

    login_tab, register_tab = st.tabs(
        ["Login", "Register"]
    )

    with login_tab:
        login_page()

    with register_tab:
        registration_page()


# ==================================================
# MAIN APPLICATION
# ==================================================

def main():

    if not st.session_state.logged_in:

        authentication_page()

        return

    user = st.session_state.user

    # Defensive check for old session data.
    if not isinstance(user, dict):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.warning("Please log in again.")
        st.rerun()
        return

    st.sidebar.title("🎓 LearnMate AI")

    st.sidebar.write("Welcome, " + user.get("name", "Student"))

    st.sidebar.caption(user["email"])

    menu = [
        "Dashboard",
        "7-Day AI Study Plan",
        "AI Tutor",
        "Diagnostic Quiz",
        "My Activity",
        "Change Password"
    ]

    if is_admin():

        st.sidebar.divider()
        st.sidebar.subheader("Admin Panel")

        menu.extend([
            "Registered Students",
            "Student Learning Records",
            "All Student Activities"
        ])

    selected_page = st.sidebar.radio(
        "Navigation",
        menu
    )

    st.sidebar.divider()

    if st.sidebar.button("Test Gemini Connection"):

        with st.spinner("Testing Gemini..."):

            success, result = test_gemini()

        if success:

            st.sidebar.success("Gemini connected.")

        else:

            st.sidebar.error("Gemini connection failed.")
            show_ai_error(result)

    if st.sidebar.button("Logout"):

        record_activity("Logout", "Student logged out.")

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()

    if selected_page == "Dashboard":
        dashboard_page()

    elif selected_page == "7-Day AI Study Plan":
        study_plan_page()

    elif selected_page == "AI Tutor":
        tutor_page()

    elif selected_page == "Diagnostic Quiz":
        quiz_page()

    elif selected_page == "My Activity":
        my_activity_page()

    elif selected_page == "Change Password":
        change_password_page()

    elif selected_page == "Registered Students" and is_admin():
        registered_students_page()

    elif selected_page == "Student Learning Records" and is_admin():
        student_learning_records_page()

    elif selected_page == "All Student Activities" and is_admin():
        all_student_activities_page()

    st.divider()

    st.caption(
        "LearnMate AI | Study Planner | AI Tutor | Diagnostic Quiz"
    )


main()
