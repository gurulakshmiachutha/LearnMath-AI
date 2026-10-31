
import streamlit as st

from database import (
    init_db,
    save_student,
    get_student,
    save_quiz_result,
    get_quiz_results,
    save_tutor_question,
    get_tutor_questions,
    get_latest_study_plan
)

from ai_tutor import (
    get_tutor_response,
    generate_study_plan
)


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="LearnMate AI",
    page_icon="📚",
    layout="wide"
)

# Initialize database
init_db()


# ==========================================
# 2. SESSION STATE
# ==========================================

if "student_email" not in st.session_state:
    st.session_state.student_email = ""

if "generated_study_plan" not in st.session_state:
    st.session_state.generated_study_plan = ""

if "last_quiz_score" not in st.session_state:
    st.session_state.last_quiz_score = None


# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("📚 LearnMate AI")

st.sidebar.caption(
    "Your Personal Adaptive Exam Tutor"
)

page = st.sidebar.radio(
    "Choose a Page",
    [
        "Home",
        "Student Registration",
        "Diagnostic Quiz",
        "Learning Dashboard",
        "AI Tutor",
        "AI Study Planner"
    ]
)

st.sidebar.divider()

st.sidebar.subheader("Student Login")

login_email = st.sidebar.text_input(
    "Enter Registered Email",
    value=st.session_state.student_email
)

if st.sidebar.button("Load Student"):

    if login_email.strip():

        student_record = get_student(
            login_email.strip()
        )

        if student_record:

            st.session_state.student_email = login_email.strip()
            st.session_state.generated_study_plan = ""

            st.sidebar.success(
                "Student loaded successfully!"
            )

        else:

            st.sidebar.error(
                "Student not found. Please register first."
            )

    else:

        st.sidebar.warning(
            "Please enter your email."
        )


# ==========================================
# 4. LOAD CURRENT STUDENT
# ==========================================

student = None

if st.session_state.student_email:

    student = get_student(
        st.session_state.student_email
    )


# ==========================================
# 5. HOME PAGE
# ==========================================

if page == "Home":

    st.title("📚 Welcome to LearnMate AI")

    st.subheader(
        "Your Personal Adaptive Exam Tutor"
    )

    st.write(
        """
        LearnMate AI is an AI-powered personalized
        learning platform designed to improve students'
        academic performance.

        It combines artificial intelligence, diagnostic
        quizzes, performance tracking and personalized
        study planning.
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        st.info("📝 Student Registration")

        st.info("🧠 Diagnostic Quiz")

        st.info("📊 Learning Dashboard")

    with col2:

        st.info("🤖 Gemini AI Tutor")

        st.info("📅 AI Study Planner")

    st.divider()

    if student:

        st.success(
            "Welcome back, " + student["name"] + "!"
        )

    else:

        st.warning(
            "Register or load your student account to begin."
        )


# ==========================================
# 6. STUDENT REGISTRATION
# ==========================================

elif page == "Student Registration":

    st.title("📝 Student Registration")

    st.write(
        "Enter your details to create your LearnMate account."
    )

    with st.form("registration_form"):

        name = st.text_input("Full Name")

        email = st.text_input("Email Address")

        course = st.text_input(
            "Course",
            value="B.Tech CSE"
        )

        subject = st.selectbox(
            "Select Your Subject",
            [
                "Python",
                "Java",
                "C Programming",
                "Data Structures",
                "Database Management Systems",
                "Computer Networks",
                "Operating Systems"
            ]
        )

        level = st.selectbox(
            "Academic Level",
            [
                "Beginner",
                "Intermediate",
                "Advanced"
            ]
        )

        study_hours = st.number_input(
            "Daily Study Hours",
            min_value=1,
            max_value=12,
            value=3
        )

        submitted = st.form_submit_button(
            "Register Student"
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.error(
                    "Please enter your name and email."
                )

            elif "@" not in email or "." not in email:

                st.error(
                    "Please enter a valid email address."
                )

            else:

                try:

                    save_student(
                        name.strip(),
                        email.strip(),
                        subject,
                        level,
                        study_hours
                    )

                    # Update course separately if supported
                    from database import get_connection

                    conn = get_connection()

                    cursor = conn.cursor()

                    cursor.execute(
                        "UPDATE students SET course = ? WHERE email = ?",
                        (course, email.strip())
                    )

                    conn.commit()
                    conn.close()

                    st.session_state.student_email = email.strip()

                    st.session_state.generated_study_plan = ""

                    st.success(
                        "Registration successful!"
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        "Registration failed."
                    )

                    st.code(str(error))


# ==========================================
# 7. DIAGNOSTIC QUIZ
# ==========================================

elif page == "Diagnostic Quiz":

    st.title("🧠 Diagnostic Quiz")

    if student is None:

        st.warning(
            "Please register or load your student account first."
        )

    else:

        st.write(
            "Student: " + student["name"]
        )

        quiz_subject = st.selectbox(
            "Choose Quiz Subject",
            [
                "Python",
                "Java",
                "C Programming",
                "Data Structures"
            ]
        )

        questions = [

            {
                "question": "Which keyword defines a function in Python?",
                "options": ["function", "def", "fun", "define"],
                "answer": "def"
            },

            {
                "question": "Which data type stores True or False?",
                "options": ["int", "str", "bool", "float"],
                "answer": "bool"
            },

            {
                "question": "Which symbol is used for comments in Python?",
                "options": ["//", "#", "/*", "--"],
                "answer": "#"
            },

            {
                "question": "Which method adds an item to a Python list?",
                "options": ["add()", "insertEnd()", "append()", "push()"],
                "answer": "append()"
            },

            {
                "question": "Which loop iterates over a sequence?",
                "options": ["for", "switch", "case", "goto"],
                "answer": "for"
            }

        ]

        with st.form("quiz_form"):

            answers = []

            for index, question in enumerate(questions):

                st.write(
                    "**Q" + str(index + 1) + ". " +
                    question["question"] + "**"
                )

                answer = st.radio(
                    "Select your answer",
                    question["options"],
                    key="question_" + str(index)
                )

                answers.append(answer)

            quiz_submitted = st.form_submit_button(
                "Submit Quiz"
            )

            if quiz_submitted:

                score = 0

                for index, question in enumerate(questions):

                    if answers[index] == question["answer"]:

                        score += 1

                save_quiz_result(
                    student["email"],
                    quiz_subject,
                    score,
                    len(questions)
                )

                st.session_state.last_quiz_score = score

                st.success(
                    "Quiz submitted successfully!"
                )

                st.metric(
                    "Your Score",
                    str(score) + "/" + str(len(questions))
                )

                percentage = (
                    score / len(questions)
                ) * 100

                st.progress(int(percentage))

                st.write(
                    "Your Performance: " +
                    str(round(percentage, 2)) + "%"
                )


# ==========================================
# 8. LEARNING DASHBOARD
# ==========================================

elif page == "Learning Dashboard":

    st.title("📊 Learning Dashboard")

    if student is None:

        st.warning(
            "Please register or load your student account."
        )

    else:

        st.subheader(
            "Welcome, " + student["name"]
        )

        results = get_quiz_results(
            student["email"]
        )

        if results:

            total_score = 0

            total_questions = 0

            for result in results:

                total_score += result["score"]

                total_questions += result["total_questions"]

            if total_questions > 0:

                percentage = (
                    total_score / total_questions
                ) * 100

            else:

                percentage = 0

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Quizzes",
                len(results)
            )

            col2.metric(
                "Total Score",
                str(total_score) + "/" + str(total_questions)
            )

            col3.metric(
                "Average Performance",
                str(round(percentage, 2)) + "%"
            )

            st.subheader("Quiz History")

            for result in results:

                st.write(
                    result["subject"] + " : " +
                    str(result["score"]) + "/" +
                    str(result["total_questions"])
                )

        else:

            st.info(
                "Complete a diagnostic quiz to see your performance."
            )

        st.divider()

        st.subheader("Student Details")

        st.write("Course:", student["course"])

        st.write("Subject:", student["subject"])

        st.write("Level:", student["level"])

        st.write(
            "Daily Study Hours:",
            student["study_hours"]
        )


# ==========================================
# 9. AI TUTOR
# ==========================================

elif page == "AI Tutor":

    st.title("🤖 Gemini AI Tutor")

    st.write(
        "Ask questions and receive AI-powered explanations."
    )

    if student is None:

        st.warning(
            "Please register or load your student account first."
        )

    else:

        tutor_subject = st.selectbox(
            "Select Subject",
            [
                "Python",
                "Java",
                "C Programming",
                "Data Structures",
                "Database Management Systems"
            ]
        )

        answer_type = st.selectbox(
            "Choose Answer Style",
            [
                "Simple Explanation",
                "Step-by-Step Explanation",
                "Exam Answer",
                "With Examples"
            ]
        )

        question = st.text_area(
            "Enter Your Question"
        )

        if st.button("Ask Gemini"):

            if not question.strip():

                st.warning(
                    "Please enter your question."
                )

            else:

                try:

                    with st.spinner(
                        "Gemini is preparing your answer..."
                    ):

                        answer = get_tutor_response(
                            question,
                            tutor_subject,
                            student["level"],
                            answer_type
                        )

                    st.subheader("AI Tutor Answer")

                    st.markdown(answer)

                    save_tutor_question(
                        student["email"],
                        tutor_subject,
                        question,
                        answer
                    )

                except Exception as error:

                    st.error(
                        "Gemini could not generate an answer."
                    )

                    st.code(str(error))

        st.divider()

        st.subheader("Previous Questions")

        previous_questions = get_tutor_questions(
            student["email"]
        )

        if previous_questions:

            for item in previous_questions:

                with st.expander(item["question"]):

                    st.markdown(item["answer"])

        else:

            st.info(
                "No previous questions available."
            )


# ==========================================
# 10. AI STUDY PLANNER
# ==========================================

elif page == "AI Study Planner":

    st.title("📅 AI Study Planner")

    st.write(
        "Generate your personalized seven-day study schedule."
    )

    if student is None:

        st.warning(
            "Please register or load your student account first."
        )

    else:

        st.subheader("Student Information")

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                "**Name:**",
                student["name"]
            )

            st.write(
                "**Subject:**",
                student["subject"]
            )

            st.write(
                "**Academic Level:**",
                student["level"]
            )

        with col2:

            st.write(
                "**Daily Study Hours:**",
                student["study_hours"]
            )

            st.write(
                "**Email:**",
                student["email"]
            )

        quiz_results = get_quiz_results(
            student["email"]
        )

        st.divider()

        st.subheader("Your Quiz Performance")

        if quiz_results:

            for result in quiz_results:

                st.write(
                    result["subject"] + " : " +
                    str(result["score"]) + "/" +
                    str(result["total_questions"])
                )

        else:

            st.info(
                "No quiz results found. "
                "You can still generate a study plan."
            )

        st.divider()

        if st.button(
            "✨ Generate My Study Plan",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Gemini is generating your personalized plan. Please wait..."
                ):

                    plan = generate_study_plan(
                        student,
                        quiz_results
                    )

                st.session_state.generated_study_plan = plan

                st.success(
                    "Your study plan was generated successfully!"
                )

            except Exception as error:

                st.error(
                    "Study plan generation failed."
                )

                if (
                    "504" in str(error)
                    or "DEADLINE_EXCEEDED" in str(error)
                ):

                    st.warning(
                        "Gemini took too long to respond. "
                        "Please wait and try again."
                    )

                else:

                    st.code(str(error))

        if st.session_state.generated_study_plan:

            st.divider()

            st.subheader(
                "📚 Your Personalized 7-Day Study Plan"
            )

            st.markdown(
                st.session_state.generated_study_plan
            )

            st.download_button(
                "Download Study Plan",
                data=st.session_state.generated_study_plan,
                file_name="LearnMate_Study_Plan.txt",
                mime="text/plain"
            )

        else:

            try:

                previous_plan = get_latest_study_plan(
                    student["email"]
                )

                if previous_plan:

                    st.subheader(
                        "Previously Saved Study Plan"
                    )

                    st.markdown(
                        previous_plan["plan"]
                    )

            except Exception as error:

                st.warning(
                    "Could not load the previously saved plan."
                )

                st.code(str(error))


# ==========================================
# 11. FOOTER
# ==========================================

st.sidebar.divider()

st.sidebar.caption(
    "LearnMate AI"
)

st.sidebar.caption(
    "Powered by Python, Streamlit, SQLite and Gemini AI"
)
