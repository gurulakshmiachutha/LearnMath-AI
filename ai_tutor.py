
# LEARNMATE AI - OFFLINE TUTOR AND STUDY PLANNER

def get_tutor_response(question, subject, level, answer_type):

    question_lower = question.lower()
    subject_lower = subject.lower()

    answer = ""

    # PYTHON TUTOR
    if "python" in subject_lower:

        if "variable" in question_lower:
            answer = """
PYTHON VARIABLES

A variable is a name used to store data.

Example:
name = "Lakshmi"
age = 20

print(name)
print(age)

Output:
Lakshmi
20

Explanation:
name stores text.
age stores a number.

Practice:
1. Create a variable for your name.
2. Create a variable for your age.
3. Print both variables.
"""

        elif "loop" in question_lower:
            answer = """
PYTHON LOOPS

Loops are used to repeat instructions.

Types:
1. for loop
2. while loop

Example:

for i in range(1, 6):
    print(i)

Output:
1
2
3
4
5

Practice:
Write a loop to print numbers from 1 to 10.
"""

        elif "list" in question_lower:
            answer = """
PYTHON LISTS

A list stores multiple values in one variable.

Example:

marks = [80, 90, 75, 85]

print(marks[0])

Output:
80

Important points:
- Lists use square brackets.
- List indexing starts from 0.
- Lists can store multiple values.

Practice:
Create a list containing five subjects.
"""

        elif "function" in question_lower:
            answer = """
PYTHON FUNCTIONS

A function is a reusable block of code.

Example:

def greet():
    print("Hello Student")

greet()

Output:
Hello Student

Benefits:
1. Code reusability.
2. Better organization.
3. Less repetition.

Practice:
Write a function that prints your name.
"""

        elif "if" in question_lower or "condition" in question_lower:
            answer = """
PYTHON CONDITIONAL STATEMENTS

Conditional statements execute code based on a condition.

Example:

marks = 80

if marks >= 40:
    print("Pass")
else:
    print("Fail")

Output:
Pass

Important keywords:
- if
- elif
- else

Practice:
Write a program to check whether a number is positive or negative.
"""

        elif "string" in question_lower:
            answer = """
PYTHON STRINGS

A string is a collection of characters.

Example:

name = "Lakshmi"

print(name)
print(name.upper())
print(len(name))

Output:
Lakshmi
LAKSHMI
7

Practice:
Create a string and print it in uppercase.
"""

        elif "dictionary" in question_lower:
            answer = """
PYTHON DICTIONARIES

A dictionary stores information as key-value pairs.

Example:

student = {
    "name": "Lakshmi",
    "age": 20
}

print(student["name"])

Output:
Lakshmi

Practice:
Create a dictionary containing student name, age and course.
"""

        else:
            answer = f"""
PYTHON - LEARNING EXPLANATION

Topic: {question}

Let's understand the topic step by step.

1. Understand the basic definition.
2. Learn the important concepts.
3. Study a simple Python example.
4. Practice writing the code.
5. Test your understanding.

Practice Activities:
- Write a small Python program.
- Identify the important keywords.
- Solve five related questions.

Revision:
Explain the concept in your own words.
"""

    # JAVA TUTOR
    elif "java" in subject_lower:

        if "class" in question_lower:
            answer = """
JAVA CLASSES AND OBJECTS

A class is a blueprint for creating objects.

Example:

class Student {
    void display() {
        System.out.println("Hello Student");
    }
}

A class contains variables and methods.

An object is an instance of a class.

Practice:
Create a Student class with name and age.
"""

        elif "inheritance" in question_lower:
            answer = """
JAVA INHERITANCE

Inheritance allows one class to acquire properties
and methods of another class.

Example:

class Animal {
    void eat() {
        System.out.println("Eating");
    }
}

class Dog extends Animal {
    void bark() {
        System.out.println("Barking");
    }
}

Practice:
Create a Parent class and Child class.
"""

        else:
            answer = f"""
JAVA LEARNING EXPLANATION

Topic: {question}

1. Understand the definition.
2. Learn the syntax.
3. Study a Java example.
4. Practice coding.
5. Revise important concepts.
"""

    # GENERAL SUBJECT TUTOR
    else:
        answer = f"""
PERSONALIZED SUBJECT TUTOR

Subject: {subject}
Topic: {question}

Explanation:

1. Introduction:
Understand the basic meaning of the topic.

2. Important Concepts:
Identify the main points and definitions.

3. Learning:
Read the concepts and understand examples.

4. Practice:
Solve five questions related to this topic.

5. Revision:
Write short notes and revise the important points.

Learning Tip:
Study in small sections and test your understanding
after each section.
"""

    return f"""
LEARNMATE AI - PERSONAL TUTOR

Subject: {subject}
Student Level: {level}
Answer Style: {answer_type}

{answer}

END OF TUTOR RESPONSE
"""


# PERSONALIZED STUDY PLAN

def generate_study_plan(student, quiz_results):

    name = student["name"]
    email = student["email"]
    subject = student["subject"]
    level = student["level"]
    hours = student["study_hours"]

    weak_topics = []

    for result in quiz_results:

        if result["total_questions"] > 0:

            percentage = (
                result["score"] /
                result["total_questions"]
            ) * 100

            if percentage < 70:
                weak_topics.append(result["subject"])

    if weak_topics:
        focus = ", ".join(weak_topics)
    else:
        focus = subject + " fundamentals"

    plan = f"""
====================================
       LEARNMATE AI
  PERSONALIZED 7-DAY STUDY PLAN
====================================

Student Name: {name}
Subject: {subject}
Level: {level}
Daily Study Hours: {hours}

Weak Areas:
{focus}


DAY 1 - BASIC CONCEPTS
---------------------
1. Understand fundamental concepts.
2. Read important definitions.
3. Practice five questions.
4. Revise today's learning.


DAY 2 - IMPORTANT TOPICS
-----------------------
1. Study two important topics.
2. Understand solved examples.
3. Practice ten questions.
4. Write short notes.


DAY 3 - PROBLEM SOLVING
----------------------
1. Solve practical problems.
2. Practice previous questions.
3. Identify mistakes.
4. Revise difficult concepts.


DAY 4 - WEAK AREA IMPROVEMENT
----------------------------
1. Focus on difficult topics.
2. Study solved examples.
3. Practice related questions.
4. Revise important concepts.


DAY 5 - APPLICATION
-------------------
1. Study real-world applications.
2. Solve advanced questions.
3. Complete one topic test.
4. Review your mistakes.


DAY 6 - COMPLETE REVISION
------------------------
1. Revise all studied topics.
2. Prepare short notes.
3. Take a mock test.
4. Identify remaining weak areas.


DAY 7 - FINAL ASSESSMENT
-----------------------
1. Revise important concepts.
2. Take a final practice test.
3. Check your answers.
4. Review your performance.


DAILY ROUTINE
-------------
- Learn new concepts.
- Practice questions.
- Revise previous topics.
- Take a short self-assessment.

====================================
Generated by LearnMate AI
====================================

Note: This study plan is generated locally.
It does not require an internet connection.
"""

    # Save plan in database
    from database import save_study_plan

    save_study_plan(email, subject, plan)

    return plan
