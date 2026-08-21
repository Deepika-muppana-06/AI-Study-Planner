from flask import Flask, render_template, request, redirect, url_for, session
from config import db, model
from datetime import date

import markdown

app = Flask(__name__)
app.secret_key = "ai-study-planner-secret-key"

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        print(request.form)

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        values = (name, email, password)

        cursor.execute(query, values)
        db.commit()

        print("User Registered Successfully!")
        print("Name:", name)
        print("Email:", email)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        query = "SELECT * FROM users WHERE email=%s AND password=%s"
        values = (email, password)

        cursor.execute(query, values)

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['user_name'] = user[1]

            return redirect(url_for('dashboard'))
        else:
            return "Invalid Email or Password"

    return render_template('login.html')

@app.route('/add_subject', methods=['GET','POST'])
def add_subject():

    if request.method == 'POST':

        subject_name = request.form['subject_name']

        cursor = db.cursor()

        query = """
        INSERT INTO subjects
        (user_id, subject_name)
        VALUES (%s,%s)
        """

        values = (session['user_id'], subject_name)

        cursor.execute(query, values)

        db.commit()

        return redirect(url_for('dashboard'))


    return render_template('add_subject.html')


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    # Get all subjects of current user
    cursor.execute("""
        SELECT subject_name
        FROM subjects
        WHERE user_id=%s
        ORDER BY subject_name
    """, (session['user_id'],))

    subjects = cursor.fetchall()

    if request.method == 'POST':

        subject = request.form['subject']
        task_name = request.form['task_name']
        deadline = request.form['deadline']
        status = request.form['status']

        query = """
        INSERT INTO tasks
        (user_id, subject, task_name, deadline, status)
        VALUES (%s,%s,%s,%s,%s)
        """

        values = (
            session['user_id'],
            subject,
            task_name,
            deadline,
            status
        )

        cursor.execute(query, values)
        db.commit()

        return redirect(url_for('dashboard'))

    return render_template(
        'add_task.html',
        subjects=subjects
    )

@app.route('/edit_task/<int:task_id>', methods=['GET','POST'])
def edit_task(task_id):

    user_id = session.get("user_id")

    cursor = db.cursor()


    if request.method == "POST":


        subject = request.form['subject']

        task_name = request.form['task_name']

        deadline = request.form['deadline']

        status = request.form['status']



        cursor.execute(
            """
            UPDATE tasks
            SET subject=%s,
                task_name=%s,
                deadline=%s,
                status=%s
            WHERE id=%s
            AND user_id=%s
            """,
            (
                subject,
                task_name,
                deadline,
                status,
                task_id,
                user_id
            )
        )


        db.commit()


        return redirect('/tasks')





    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE id=%s
        AND user_id=%s
        """,
        (
            task_id,
            user_id
        )
    )


    task = cursor.fetchone()



    return render_template(
        "edit_task.html",
        task=task
    )


@app.route('/tasks')
def tasks():

    user_id = session.get("user_id")

    cursor = db.cursor()


    cursor.execute(
        """
        SELECT 
        task_id,
        subject,
        task_name,
        deadline,
        status

        FROM tasks

        WHERE user_id=%s

        ORDER BY task_id DESC
        """,
        (user_id,)
    )


    tasks = cursor.fetchall()


    return render_template(
        "tasks.html",
        tasks=tasks
    )

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):

    user_id = session.get("user_id")

    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM tasks
        WHERE task_id=%s
        AND user_id=%s
        """,
        (task_id,user_id)
    )


    db.commit()


    return redirect('/tasks')

@app.route('/add_exam', methods=['GET','POST'])
def add_exam():

    if request.method == 'POST':

        subject = request.form['subject']
        exam_name = request.form['exam_name']
        exam_date = request.form['exam_date']


        cursor = db.cursor()

        query = """
        INSERT INTO exams
        (user_id, subject, exam_name, exam_date)
        VALUES (%s,%s,%s,%s)
        """

        values = (
        session['user_id'],
        subject,
        exam_name,
        exam_date
    )


        cursor.execute(query, values)

        db.commit()


        return redirect(url_for('dashboard'))


    return render_template('add_exam.html')


@app.route('/add_schedule', methods=['GET','POST'])
def add_schedule():

    if request.method == 'POST':

        study_date = request.form['study_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        topic = request.form['topic']


        cursor = db.cursor()


        query = """
        INSERT INTO study_schedule
        (user_id, study_date, start_time, end_time, topic)
        VALUES (%s,%s,%s,%s,%s)
        """


        values = (
    session['user_id'],
    study_date,
    start_time,
    end_time,
    topic
)


        cursor.execute(query, values)

        db.commit()


        return redirect(url_for('dashboard'))


    return render_template('add_schedule.html')

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


@app.route('/ai_planner', methods=['GET','POST'])
def ai_planner():

    if request.method == "POST":

        hours = request.form.get("hours")
        subjects = request.form.get("subjects")
        exam_date = request.form.get("exam_date")

        goal = request.form.get("goal")
        level = request.form.get("level")
        style = request.form.get("style")
        weak_topics = request.form.get("weak_topics")
        routine = request.form.get("routine")
        priority = request.form.get("priority")
        plan_type = request.form.get("plan_type")


        subjects_list = subjects.split(",")


        subject_plan = ""

        for i, sub in enumerate(subjects_list):

            sub = sub.strip()

            subject_plan += f"""
{i+1}. {sub}
"""


        morning = subjects_list[0].strip()


        if len(subjects_list) > 1:
            afternoon = subjects_list[1].strip()
        else:
            afternoon = morning


        prompt = f"""

        You are an AI Study Planner.

        Create a concise, practical and personalized study plan.

        User Details:

        Goal: {goal}
        Subjects: {subjects}
        Daily Hours: {hours}
        Exam Date: {exam_date}
        Current Level: {level}
        Learning Style: {style}
        Weak Topics: {weak_topics}
        Routine: {routine}
        Priority: {priority}


        IMPORTANT OUTPUT FORMAT:

        Do NOT write a long essay.

        Use short sections, tables and bullet points.

        Format:

        # 🤖 AI Study Plan


        ## 📌 Overview Table

        | Item | Details |
        |---|---|
        | Goal | |
        | Subjects | |
        | Exam Date | |
        | Daily Hours | |
        | Level | |


        ## 🗓️ Study Roadmap

        | Day/Week | Topic | Task |
        |---|---|---|
        | | | |


        ## ⏰ Daily Schedule

        | Time | Activity |
        |---|---|
        | Morning | |
        | Afternoon | |
        | Evening | |


        ## 🔥 Focus Areas

        - 
        - 


        ## 💡 Tips

        - 


        Keep the plan within 700-900 words maximum.
        Make it easy to read.
        """


        response = model.generate_content(prompt)

        plan = response.text
        cursor = db.cursor()

        query = """
        INSERT INTO ai_plans
        (user_id, subjects, hours, exam_date, plan_text)
        VALUES (%s,%s,%s,%s,%s)
        """
        values = (
            session['user_id'],
            subjects,
            hours,
            exam_date,
            plan
        )
        cursor.execute(query, values)

        db.commit()
        return redirect('/my_plans')

    return render_template('ai_planner.html')

@app.route('/my_plans')
def my_plans():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM ai_plans
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (session['user_id'],)
    )

    plans = cursor.fetchall()
    return render_template(
        'plans.html',
        plans=plans
    )

@app.route('/subjects')
def subjects():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    # Get all subjects
    cursor.execute("""
        SELECT *
        FROM subjects
        WHERE user_id=%s
        ORDER BY subject_name
    """, (session['user_id'],))

    subjects = cursor.fetchall()

    subject_data = []

    for subject in subjects:

        subject_name = subject['subject_name']

        # Total Tasks
        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE user_id=%s
            AND subject=%s
        """, (session['user_id'], subject_name))

        total_tasks = cursor.fetchone()['COUNT(*)']

        # Completed Tasks
        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE user_id=%s
            AND subject=%s
            AND status='Completed'
        """, (session['user_id'], subject_name))

        completed_tasks = cursor.fetchone()['COUNT(*)']

        pending_tasks = total_tasks - completed_tasks

        # Upcoming Exams
        cursor.execute("""
            SELECT COUNT(*)
            FROM exams
            WHERE user_id=%s
            AND subject=%s
            AND exam_date>=CURDATE()
        """, (session['user_id'], subject_name))

        upcoming_exams = cursor.fetchone()['COUNT(*)']

        # Study Schedule
        cursor.execute("""
            SELECT COUNT(*)
            FROM schedules
            WHERE user_id=%s
            AND subject=%s
        """, (session['user_id'], subject_name))

        schedules = cursor.fetchone()['COUNT(*)']

        # Progress
        if total_tasks == 0:
            progress = 0
        else:
            progress = int((completed_tasks / total_tasks) * 100)

        # Progress Status
        if progress == 100:
            status = "🏆 Completed"
        elif progress >= 75:
            status = "🔥 Excellent"
        elif progress >= 40:
            status = "🚀 In Progress"
        else:
            status = "📖 Needs Attention"

        subject_data.append({
            "name": subject_name,
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "exams": upcoming_exams,
            "schedules": schedules,
            "progress": progress,
            "status": status
        })

    return render_template(
        "subjects.html",
        subjects=subject_data
    )

@app.route('/schedule')
def schedule():

    user_id = session.get("user_id")

    cursor = db.cursor()


    cursor.execute(
        """
        SELECT start_time, end_time, topic, study_date
        FROM study_schedule
        WHERE user_id=%s
        ORDER BY study_date, start_time
        """,
        (user_id,)
    )


    schedules = cursor.fetchall()


    return render_template(
        "schedule.html",
        schedules=schedules
    )


@app.route('/progress')
def progress():

    user_id = session.get("user_id")

    cursor = db.cursor()


    # Total tasks count
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE user_id=%s
        """,
        (user_id,)
    )

    total_tasks = cursor.fetchone()[0]



    # Completed tasks count
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE user_id=%s
        AND status='Completed'
        """,
        (user_id,)
    )

    completed_tasks = cursor.fetchone()[0]



    # Progress calculation
    if total_tasks == 0:

        progress = 0

    else:

        progress = int(
            (completed_tasks / total_tasks) * 100
        )

    achievements = []


    if total_tasks == 0:

        achievements.append({
            "icon":"🌱",
            "title":"Start your journey",
            "percent":0
        })


    elif progress == 100:

        achievements.append({
            "icon":"👑",
            "title":"Study Master",
            "percent":100
        })


    elif progress >= 75:

        achievements.append({
            "icon":"🚀",
            "title":"Consistency Champion",
            "percent":75
        })


    elif progress >= 50:

        achievements.append({
            "icon":"🔥",
            "title":"Halfway Hero",
            "percent":50
        })


    elif completed_tasks >= 1:

        achievements.append({
            "icon":"🥉",
            "title":"First Step Completed",
            "percent":25
        })


    return render_template(
        "progress.html",
        user_name=session.get("user_name"),
        progress=progress,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        achievements=achievements
    )

@app.route('/view_plan/<int:plan_id>')
def view_plan(plan_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM ai_plans WHERE plan_id=%s",
        (plan_id,)
    )

    plan = cursor.fetchone()

    cursor.close()



    if plan is None:
        return "Plan not found"


    # Convert AI markdown text into proper HTML
    plan["plan_text"] = markdown.markdown(
        plan["plan_text"],
        extensions=['tables']
    )


    return render_template(
        "view_plans.html",
        plan=plan
    )

@app.route('/exams')
def exams():

    if 'user_id' not in session:
        return redirect(url_for('login'))


    cursor = db.cursor()


    cursor.execute(
        """
        SELECT *
        FROM exams
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )


    exams = cursor.fetchall()


    return render_template(
        "exams.html",
        exams=exams,
        user_name=session.get("user_name")
    )

@app.route('/delete_exam/<int:exam_id>')
def delete_exam(exam_id):

    user_id = session.get("user_id")

    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM exams
        WHERE exam_id=%s
        AND user_id=%s
        """,
        (exam_id,user_id)
    )


    db.commit()


    return redirect('/exams')


@app.route('/delete_plan/<int:plan_id>')
def delete_plan(plan_id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM ai_plans WHERE plan_id=%s",
        (plan_id,)
    )

    db.commit()

    cursor.close()

    return redirect('/my_plans')


@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))


    cursor = db.cursor()


    user_name = session['user_name']


    # Subjects count (current user)
    cursor.execute(
        "SELECT COUNT(*) FROM subjects WHERE user_id=%s",
        (session['user_id'],)
    )

    subject_count = cursor.fetchone()[0]



    # Pending tasks (current user)
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='Pending' AND user_id=%s",
        (session['user_id'],)
    )

    pending_tasks = cursor.fetchone()[0]



    # Completed tasks (current user)
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='Completed' AND user_id=%s",
        (session['user_id'],)
    )

    completed_tasks = cursor.fetchone()[0]



    # Total tasks (current user)
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=%s",
        (session['user_id'],)
    )

    total_tasks = cursor.fetchone()[0]


    # Progress calculation
    if total_tasks == 0:
        progress = 0
    else:
        progress = int((completed_tasks / total_tasks) * 100)

    # Exams count (current user)
    cursor.execute(
        "SELECT COUNT(*) FROM exams WHERE user_id=%s",
        (session['user_id'],)
    )

    exam_count = cursor.fetchone()[0]

    # Schedule (current user)
    today = date.today()
    cursor.execute(
        """
        SELECT study_date, start_time, end_time, topic
        FROM study_schedule
        WHERE user_id=%s
        AND study_date > %s
        ORDER BY study_date, start_time
        LIMIT 5
        """,
        (session['user_id'], today)
    )

    upcoming_schedules = cursor.fetchall()

    schedules = upcoming_schedules

    cursor.execute(
        """
        SELECT exam_name, subject, exam_date
        FROM exams
        WHERE user_id=%s
        AND exam_date >= %s
        ORDER BY exam_date
        LIMIT 5
        """,
        (session['user_id'], today)
    )

    upcoming_exams = cursor.fetchall()
    # Get subject names
    cursor.execute(
        """
        SELECT subject_name
        FROM subjects
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )

    subjects = cursor.fetchall()

    subject_list = ", ".join([s[0] for s in subjects])
    
    # AI Insights
    insights = []

    if pending_tasks > 0:
        insights.append(f"You have {pending_tasks} pending tasks.")

    if upcoming_exams:
        insights.append(
            f"Your next exam is on {upcoming_exams[0][2]}."
        )

    if progress < 40:
        insights.append("Try studying at least 2 hours today.")
    elif progress < 70:
        insights.append("Good progress! Keep going.")
    else:
        insights.append("Excellent! You're doing great.")

    if subject_count == 0:
        insights.append("Add subjects to organize your study plan.")


    # ================= AI Recommendations =================

    prompt = f"""
    You are an AI Study Mentor.

    Student Details

    Subjects:
    {subject_list}

    Pending Tasks:
    {pending_tasks}

    Completed Tasks:
    {completed_tasks}

    Upcoming Exams:
    {exam_count}

    Overall Progress:
    {progress}%

    Give ONLY 5 short personalized study recommendations.

    Rules:
    - Maximum 15 words each.
    - Use bullet points.
    - Don't greet.
    - Don't use markdown.
    """

    try:
        response = model.generate_content(prompt)
        recommendations = response.text
    except:
        recommendations = """
    • Complete one pending task today.
    • Revise your difficult subject.
    • Stay consistent.
    • Practice daily.
    • Keep improving.
    """

    return render_template(
    "dashboard.html",
    user_name=user_name,
    subject_count=subject_count,
    pending_tasks=pending_tasks,
    completed_tasks=completed_tasks,
    exam_count=exam_count,
    schedules=schedules,
    upcoming_schedules=upcoming_schedules,
    upcoming_exams=upcoming_exams,
    insights=insights,
    recommendations=recommendations,
    progress=progress
)
if __name__ == "__main__":
    app.run(debug=True)