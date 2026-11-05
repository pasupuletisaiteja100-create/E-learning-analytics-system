import os
import io
import base64

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import (
    Flask, render_template_string, request, redirect,
    url_for, flash
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        port=3302,
        password=os.environ["DB_PASSWORD"],
        database="elearning_analytics"
    )


BASE_STYLE = """
<style>
    body { margin:0; font-family:Arial,sans-serif; background:#f1f5f9; color:#1e293b; }
    header { background:#172554; color:white; padding:22px 30px; }
    nav { background:#172554; padding:12px 22px; display:flex; flex-wrap:wrap; gap:8px; }
    nav a { color:white; text-decoration:none; padding:10px 12px; border-radius:7px; }
    nav a:hover { background:#263b70; }
    main { max-width:1200px; margin:28px auto; padding:0 20px; }
    .card { background:white; padding:22px; border-radius:12px; margin-bottom:20px;
            box-shadow:0 3px 12px #0000000d; overflow-x:auto; }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:18px; }
    .number { font-size:32px; font-weight:bold; color:#2563eb; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { text-align:left; padding:11px; border-bottom:1px solid #e2e8f0; }
    th { background:#f8fafc; }
    input,select { padding:10px; margin:5px 8px 5px 0; border:1px solid #cbd5e1;
                   border-radius:6px; min-width:180px; }
    button,.button { display:inline-block; padding:9px 13px; border:0; border-radius:6px;
                     background:#2563eb; color:white; text-decoration:none; cursor:pointer; }
    .danger { background:#dc2626; }
    .secondary { background:#475569; }
    .message { padding:10px 14px; background:#dbeafe; border-radius:7px; margin:10px 0; }
    .actions { display:flex; gap:7px; align-items:center; }
    .actions form { margin:0; }
    a { color:#1d4ed8; }
</style>
"""

NAV = """
<nav>
    <a href="/">Dashboard</a>
    <a href="/courses">Manage Courses</a>
    <a href="/learners">Manage Learners</a>
    <a href="/enrollments">Manage Enrollments</a>
    <a href="/reports">Course Reports</a>
    <a href="/charts">Comparison Charts</a>
    <a href="/activity-trends">Weekly Activity</a>
    <a href="/inactive-enrollments">Inactive Enrolments</a>
</nav>
"""

def page(title, body):
    return render_template_string("""
    <!DOCTYPE html>
    <html><head><title>{{ title }}</title>""" + BASE_STYLE + """</head>
    <body><header><h1>E-Learning Course Analytics</h1></header>
    """ + NAV + """
    <main>
        {% with messages = get_flashed_messages() %}
          {% for message in messages %}<div class="message">{{ message }}</div>{% endfor %}
        {% endwith %}
        """ + body + """
    </main></body></html>
    """, title=title)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return "Login form submitted. Authentication is not configured yet."
    return page("Login", """
        <div class="card"><h2>Login</h2>
        <p>Authentication is not configured yet.</p><a href="/">Back to Dashboard</a></div>
    """)


@app.route("/")
def home():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM courses")
        total_courses = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM learners")
        total_learners = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM enrollments")
        total_enrollments = cursor.fetchone()["total"]
        return page("Dashboard", """
            <h2>Dashboard Overview</h2>
            <div class="cards">
                <div class="card"><p>Total Courses</p><div class="number">{{ courses }}</div>
                    <a href="/courses">Manage courses</a></div>
                <div class="card"><p>Total Learners</p><div class="number">{{ learners }}</div>
                    <a href="/learners">Manage learners</a></div>
                <div class="card"><p>Total Enrollments</p><div class="number">{{ enrollments }}</div>
                    <a href="/enrollments">Manage enrollments</a></div>
            </div><p>MySQL connection successful!</p>
        """).replace("</main>", """
            <script>
            </script>
        </main>""").replace(
            '<h2>Dashboard Overview</h2>',
            '<h2>Dashboard Overview</h2>'
        ) if False else render_template_string("""
            <!DOCTYPE html><html><head><title>Dashboard</title>""" + BASE_STYLE + """</head>
            <body><header><h1>E-Learning Course Analytics</h1></header>""" + NAV + """
            <main><h2>Dashboard Overview</h2><div class="cards">
            <div class="card"><p>Total Courses</p><div class="number">{{ courses }}</div><a href="/courses">Manage courses</a></div>
            <div class="card"><p>Total Learners</p><div class="number">{{ learners }}</div><a href="/learners">Manage learners</a></div>
            <div class="card"><p>Total Enrollments</p><div class="number">{{ enrollments }}</div><a href="/enrollments">Manage enrollments</a></div>
            </div><p>MySQL connection successful!</p></main></body></html>
            """, courses=total_courses, learners=total_learners, enrollments=total_enrollments)
    except mysql.connector.Error as error:
        return f"Database connection failed: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ------------------------- COURSES CRUD -------------------------

@app.route("/courses", methods=["GET", "POST"])
def courses():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            course_name = request.form.get("course_name", "").strip()
            category = request.form.get("category", "").strip()
            if not course_name or not category:
                flash("Course name and category are required.")
                return redirect(url_for("courses"))
            cursor.execute(
                "INSERT INTO courses (course_name, category) VALUES (%s, %s)",
                (course_name, category)
            )
            connection.commit()
            flash("Course added successfully.")
            return redirect(url_for("courses"))

        cursor.execute("SELECT course_id, course_name, category FROM courses ORDER BY course_id")
        records = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Manage Courses</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Manage Courses</h1></header>""" + NAV + """
            <main>
            {% with messages = get_flashed_messages() %}{% for m in messages %}<div class="message">{{ m }}</div>{% endfor %}{% endwith %}
            <div class="card"><h2>Add Course</h2>
            <form method="POST">
                <input name="course_name" maxlength="100" placeholder="Course name" required>
                <input name="category" maxlength="50" placeholder="Category" required>
                <button type="submit">Add Course</button>
            </form></div>
            <div class="card"><h2>Course List</h2><table>
            <tr><th>ID</th><th>Course Name</th><th>Category</th><th>Actions</th></tr>
            {% for r in records %}<tr><td>{{ r.course_id }}</td><td>{{ r.course_name }}</td><td>{{ r.category }}</td>
            <td class="actions"><a class="button" href="{{ url_for('edit_course', course_id=r.course_id) }}">Edit</a>
            <form method="POST" action="{{ url_for('delete_course', course_id=r.course_id) }}" onsubmit="return confirm('Delete this course?')">
            <button class="danger" type="submit">Delete</button></form></td></tr>
            {% else %}<tr><td colspan="4">No courses found.</td></tr>{% endfor %}
            </table></div></main></body></html>
        """, records=records)
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Course operation failed: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            name = request.form.get("course_name", "").strip()
            category = request.form.get("category", "").strip()
            if not name or not category:
                flash("Both fields are required.")
                return redirect(url_for("edit_course", course_id=course_id))
            cursor.execute("UPDATE courses SET course_name=%s, category=%s WHERE course_id=%s",
                           (name, category, course_id))
            connection.commit()
            flash("Course updated successfully.")
            return redirect(url_for("courses"))
        cursor.execute("SELECT course_id, course_name, category FROM courses WHERE course_id=%s",
                       (course_id,))
        course = cursor.fetchone()
        if not course:
            return "Course not found.", 404
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Edit Course</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Edit Course</h1></header>""" + NAV + """
            <main><div class="card"><form method="POST">
            <label>Course name</label><br><input name="course_name" maxlength="100" value="{{ course.course_name }}" required><br>
            <label>Category</label><br><input name="category" maxlength="50" value="{{ course.category }}" required><br>
            <button>Save Changes</button> <a class="button secondary" href="/courses">Cancel</a>
            </form></div></main></body></html>
        """, course=course)
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to edit course: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/courses/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM courses WHERE course_id=%s", (course_id,))
        connection.commit()
        flash("Course deleted successfully.")
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        flash("This course has enrollments. Delete or reassign those enrollments first.")
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to delete course: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    return redirect(url_for("courses"))


# ------------------------- LEARNERS CRUD -------------------------

@app.route("/learners", methods=["GET", "POST"])
def learners():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            roll_no = request.form.get("roll_no", "").strip() or None
            cursor.execute("INSERT INTO learners (roll_no) VALUES (%s)", (roll_no,))
            connection.commit()
            flash("Learner added successfully.")
            return redirect(url_for("learners"))
        cursor.execute("SELECT learner_id, roll_no FROM learners ORDER BY learner_id")
        records = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Manage Learners</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Manage Learners</h1></header>""" + NAV + """
            <main>
            {% with messages = get_flashed_messages() %}{% for m in messages %}<div class="message">{{ m }}</div>{% endfor %}{% endwith %}
            <div class="card"><h2>Add Learner</h2><form method="POST">
                <input name="roll_no" maxlength="30" placeholder="Roll number (optional)">
                <button>Add Learner</button>
            </form><p>Roll number can be left blank. Each non-empty roll number must be unique.</p></div>
            <div class="card"><h2>Learner List</h2><table>
            <tr><th>Learner ID</th><th>Roll Number</th><th>Actions</th></tr>
            {% for r in records %}<tr><td>{{ r.learner_id }}</td><td>{{ r.roll_no or "Not provided" }}</td>
            <td class="actions"><a class="button" href="{{ url_for('edit_learner', learner_id=r.learner_id) }}">Edit</a>
            <form method="POST" action="{{ url_for('delete_learner', learner_id=r.learner_id) }}" onsubmit="return confirm('Delete this learner?')">
            <button class="danger">Delete</button></form></td></tr>
            {% else %}<tr><td colspan="3">No learners found.</td></tr>{% endfor %}
            </table></div></main></body></html>
        """, records=records)
    except mysql.connector.IntegrityError as error:
        if connection:
            connection.rollback()
        flash("Could not add learner. Check whether that roll number already exists.")
        return redirect(url_for("learners"))
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Learner operation failed: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/learners/edit/<int:learner_id>", methods=["GET", "POST"])
def edit_learner(learner_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            roll_no = request.form.get("roll_no", "").strip() or None
            cursor.execute("UPDATE learners SET roll_no=%s WHERE learner_id=%s",
                           (roll_no, learner_id))
            connection.commit()
            flash("Learner updated successfully.")
            return redirect(url_for("learners"))
        cursor.execute("SELECT learner_id, roll_no FROM learners WHERE learner_id=%s", (learner_id,))
        learner = cursor.fetchone()
        if not learner:
            return "Learner not found.", 404
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Edit Learner</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Edit Learner</h1></header>""" + NAV + """
            <main><div class="card"><form method="POST">
            <p>Learner ID: {{ learner.learner_id }}</p>
            <label>Roll number (optional)</label><br>
            <input name="roll_no" maxlength="30" value="{{ learner.roll_no or '' }}">
            <br><button>Save Changes</button> <a class="button secondary" href="/learners">Cancel</a>
            </form></div></main></body></html>
        """, learner=learner)
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        flash("That roll number is already assigned to another learner.")
        return redirect(url_for("edit_learner", learner_id=learner_id))
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to edit learner: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/learners/delete/<int:learner_id>", methods=["POST"])
def delete_learner(learner_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM learners WHERE learner_id=%s", (learner_id,))
        connection.commit()
        flash("Learner deleted successfully.")
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        flash("This learner has enrollments. Delete those enrollments first.")
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to delete learner: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    return redirect(url_for("learners"))


# ------------------------- ENROLLMENTS CRUD -------------------------

@app.route("/enrollments", methods=["GET", "POST"])
def enrollments():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            learner_id = request.form.get("learner_id", type=int)
            course_id = request.form.get("course_id", type=int)
            status = request.form.get("status", "enrolled")
            if not learner_id or not course_id or status not in ("enrolled", "completed", "withdrawn"):
                flash("Select a valid learner, course, and status.")
                return redirect(url_for("enrollments"))
            cursor.execute("""
                INSERT INTO enrollments (learner_id, course_id, status)
                VALUES (%s, %s, %s)
            """, (learner_id, course_id, status))
            connection.commit()
            flash("Enrollment added successfully.")
            return redirect(url_for("enrollments"))

        cursor.execute("SELECT learner_id, roll_no FROM learners ORDER BY learner_id")
        learner_options = cursor.fetchall()
        cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
        course_options = cursor.fetchall()
        cursor.execute("""
            SELECT e.enrollment_id, e.learner_id, e.course_id, e.enrolled_at, e.status,
                   l.roll_no, c.course_name
            FROM enrollments e
            JOIN learners l ON e.learner_id=l.learner_id
            JOIN courses c ON e.course_id=c.course_id
            ORDER BY e.enrollment_id
        """)
        records = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Manage Enrollments</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Manage Enrollments</h1></header>""" + NAV + """
            <main>
            {% with messages = get_flashed_messages() %}{% for m in messages %}<div class="message">{{ m }}</div>{% endfor %}{% endwith %}
            <div class="card"><h2>Add Enrollment</h2>
            {% if learners and courses %}
            <form method="POST">
                <select name="learner_id" required><option value="">Select learner</option>
                {% for l in learners %}<option value="{{ l.learner_id }}">ID {{ l.learner_id }} - {{ l.roll_no or "No roll number" }}</option>{% endfor %}</select>
                <select name="course_id" required><option value="">Select course</option>
                {% for c in courses %}<option value="{{ c.course_id }}">{{ c.course_name }}</option>{% endfor %}</select>
                <select name="status"><option value="enrolled">Enrolled</option><option value="completed">Completed</option><option value="withdrawn">Withdrawn</option></select>
                <button>Add Enrollment</button>
            </form>
            {% else %}<p>Add at least one learner and one course before creating an enrollment.</p>{% endif %}
            </div>
            <div class="card"><h2>Enrollment List</h2><table>
            <tr><th>ID</th><th>Learner ID</th><th>Roll Number</th><th>Course ID</th><th>Course</th><th>Enrolled At</th><th>Status</th><th>Actions</th></tr>
            {% for r in records %}<tr><td>{{ r.enrollment_id }}</td><td>{{ r.learner_id }}</td>
            <td>{{ r.roll_no or "Not provided" }}</td><td>{{ r.course_id }}</td><td>{{ r.course_name }}</td>
            <td>{{ r.enrolled_at or "Unknown" }}</td><td>{{ r.status }}</td>
            <td class="actions"><a class="button" href="{{ url_for('edit_enrollment', enrollment_id=r.enrollment_id) }}">Edit</a>
            <form method="POST" action="{{ url_for('delete_enrollment', enrollment_id=r.enrollment_id) }}" onsubmit="return confirm('Delete this enrollment?')">
            <button class="danger">Delete</button></form></td></tr>
            {% else %}<tr><td colspan="8">No enrollments found.</td></tr>{% endfor %}
            </table></div></main></body></html>
        """, learners=learner_options, courses=course_options, records=records)
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Enrollment operation failed: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/enrollments/edit/<int:enrollment_id>", methods=["GET", "POST"])
def edit_enrollment(enrollment_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == "POST":
            learner_id = request.form.get("learner_id", type=int)
            course_id = request.form.get("course_id", type=int)
            status = request.form.get("status")
            if not learner_id or not course_id or status not in ("enrolled", "completed", "withdrawn"):
                flash("Select valid enrollment details.")
                return redirect(url_for("edit_enrollment", enrollment_id=enrollment_id))
            cursor.execute("""
                UPDATE enrollments SET learner_id=%s, course_id=%s, status=%s
                WHERE enrollment_id=%s
            """, (learner_id, course_id, status, enrollment_id))
            connection.commit()
            flash("Enrollment updated successfully.")
            return redirect(url_for("enrollments"))

        cursor.execute("SELECT enrollment_id, learner_id, course_id, status FROM enrollments WHERE enrollment_id=%s",
                       (enrollment_id,))
        record = cursor.fetchone()
        if not record:
            return "Enrollment not found.", 404
        cursor.execute("SELECT learner_id, roll_no FROM learners ORDER BY learner_id")
        learner_options = cursor.fetchall()
        cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
        course_options = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Edit Enrollment</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Edit Enrollment #{{ record.enrollment_id }}</h1></header>""" + NAV + """
            <main><div class="card"><form method="POST">
            <label>Learner</label><br><select name="learner_id" required>
            {% for l in learners %}<option value="{{ l.learner_id }}" {% if l.learner_id == record.learner_id %}selected{% endif %}>
            ID {{ l.learner_id }} - {{ l.roll_no or "No roll number" }}</option>{% endfor %}</select><br>
            <label>Course</label><br><select name="course_id" required>
            {% for c in courses %}<option value="{{ c.course_id }}" {% if c.course_id == record.course_id %}selected{% endif %}>{{ c.course_name }}</option>{% endfor %}</select><br>
            <label>Status</label><br><select name="status">
            {% for s in statuses %}<option value="{{ s }}" {% if s == record.status %}selected{% endif %}>{{ s|capitalize }}</option>{% endfor %}</select><br>
            <button>Save Changes</button> <a class="button secondary" href="/enrollments">Cancel</a>
            </form></div></main></body></html>
        """, record=record, learners=learner_options, courses=course_options,
             statuses=["enrolled", "completed", "withdrawn"])
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to edit enrollment: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/enrollments/delete/<int:enrollment_id>", methods=["POST"])
def delete_enrollment(enrollment_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM enrollments WHERE enrollment_id=%s", (enrollment_id,))
        connection.commit()
        flash("Enrollment deleted successfully.")
    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return f"Unable to delete enrollment: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    return redirect(url_for("enrollments"))


# ------------------------- EXISTING ANALYTICS -------------------------

@app.route("/reports")
def reports():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.course_id, c.course_name, c.category,
                   COUNT(e.enrollment_id) AS total_enrollments,
                   COALESCE(SUM(CASE WHEN e.status='completed' THEN 1 ELSE 0 END),0)
                       AS completed_enrollments,
                   ROUND(100.0 * COALESCE(SUM(CASE WHEN e.status='completed' THEN 1 ELSE 0 END),0)
                       / NULLIF(COUNT(e.enrollment_id),0),2) AS completion_rate
            FROM courses c LEFT JOIN enrollments e ON c.course_id=e.course_id
            GROUP BY c.course_id,c.course_name,c.category ORDER BY c.course_name
        """)
        course_reports = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Course Reports</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Course Analytics Report</h1></header>""" + NAV + """
            <main><div class="card"><p>Completion rate = completed enrollments / total enrollments × 100</p>
            <table><tr><th>Course</th><th>Category</th><th>Enrollments</th><th>Completed</th><th>Completion Rate</th></tr>
            {% for c in reports %}<tr><td>{{ c.course_name }}</td><td>{{ c.category }}</td><td>{{ c.total_enrollments }}</td>
            <td>{{ c.completed_enrollments }}</td><td>{{ c.completion_rate if c.completion_rate is not none else "N/A" }}{% if c.completion_rate is not none %}%{% endif %}</td></tr>
            {% else %}<tr><td colspan="5">No course records.</td></tr>{% endfor %}
            </table></div></main></body></html>
        """, reports=course_reports)
    except mysql.connector.Error as error:
        return f"Report error: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/charts")
def charts():
    connection = None
    try:
        connection = get_db_connection()
        df = pd.read_sql("""
            SELECT c.course_id,c.course_name,c.category,COUNT(e.enrollment_id) AS enrollments,
                   COALESCE(SUM(CASE WHEN e.status='completed' THEN 1 ELSE 0 END),0) AS completed
            FROM courses c LEFT JOIN enrollments e ON c.course_id=e.course_id
            GROUP BY c.course_id,c.course_name,c.category ORDER BY c.course_id
        """, connection)
    except Exception as error:
        return f"Chart error: {error}", 500
    finally:
        if connection and connection.is_connected():
            connection.close()
    if df.empty:
        return page("Charts", "<div class='card'>No course records available.</div>")
    df["label"] = df["course_name"] + " (" + df["category"] + ", ID " + df["course_id"].astype(str) + ")"
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df))
    width = 0.36
    ax.bar(x - width/2, df["enrollments"], width, label="Enrollments")
    ax.bar(x + width/2, df["completed"], width, label="Completed")
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"], rotation=40, ha="right")
    ax.set_ylabel("Number of enrollments")
    ax.set_title("Course Enrollment vs Completion")
    ax.legend()
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    chart = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return render_template_string("""
        <!DOCTYPE html><html><head><title>Comparison Charts</title>""" + BASE_STYLE + """</head>
        <body><header><h1>Course Analytics Charts</h1></header>""" + NAV + """
        <main><div class="card"><h2>Enrollment vs Completion</h2>
        <img src="data:image/png;base64,{{ chart }}" alt="Course comparison chart" style="max-width:100%;height:auto;">
        </div></main></body></html>
    """, chart=chart)


@app.route("/activity-trends")
def activity_trends():
    connection = None
    try:
        connection = get_db_connection()
        df = pd.read_sql("SELECT activity_date, activity_type, completed FROM activities ORDER BY activity_date", connection)
    except Exception as error:
        return f"Activity report error: {error}", 500
    finally:
        if connection and connection.is_connected():
            connection.close()
    if df.empty:
        return page("Weekly Activity", "<div class='card'><h2>No activity records available yet.</h2></div>")
    df["activity_date"] = pd.to_datetime(df["activity_date"])
    df["week"] = df["activity_date"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly = df.groupby("week").agg(
        total_activities=("activity_type", "count"),
        completed_activities=("completed", "sum")
    ).reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(weekly["week"], weekly["total_activities"], marker="o", label="Recorded activities")
    ax.plot(weekly["week"], weekly["completed_activities"], marker="o", label="Completed activities")
    ax.set_title("Weekly Learning Activity Trends")
    ax.set_xlabel("Week")
    ax.set_ylabel("Number of activities")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    chart = base64.b64encode(buffer.getvalue()).decode("utf-8")
    table = weekly.to_html(index=False, classes="activity-table", border=1)
    return render_template_string("""
        <!DOCTYPE html><html><head><title>Weekly Activity</title>""" + BASE_STYLE + """</head>
        <body><header><h1>Weekly Learning Activity Trends</h1></header>""" + NAV + """
        <main><div class="card"><img src="data:image/png;base64,{{ chart }}" alt="Weekly activity trends" style="max-width:100%;height:auto;">
        <h2>Weekly Summary</h2>{{ table|safe }}
        <p>These values represent recorded activities only. Missing records do not prove that learning did not occur.</p>
        </div></main></body></html>
    """, chart=chart, table=table)


@app.route("/inactive-enrollments")
def inactive_enrollments():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.enrollment_id,l.roll_no,c.course_name,c.category,e.enrolled_at,
                   MAX(a.activity_date) AS last_activity
            FROM enrollments e
            JOIN learners l ON e.learner_id=l.learner_id
            JOIN courses c ON e.course_id=c.course_id
            LEFT JOIN activities a ON e.enrollment_id=a.enrollment_id
            WHERE e.status='enrolled'
            GROUP BY e.enrollment_id,l.roll_no,c.course_name,c.category,e.enrolled_at
            HAVING MAX(a.activity_date) IS NULL OR MAX(a.activity_date) <
                   DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 14 DAY)
            ORDER BY last_activity ASC
        """)
        records = cursor.fetchall()
        return render_template_string("""
            <!DOCTYPE html><html><head><title>Inactive Enrollments</title>""" + BASE_STYLE + """</head>
            <body><header><h1>Inactive Enrollment Report</h1></header>""" + NAV + """
            <main><div class="card"><p>Rule: No recorded activity during the previous 14 days. Completed enrollments are excluded.</p>
            <p>This is a review flag, not proof of lack of learning.</p><h2>Enrollments to Review: {{ records|length }}</h2>
            <table><tr><th>Enrollment ID</th><th>Roll Number</th><th>Course</th><th>Category</th><th>Enrolled At</th><th>Last Activity</th></tr>
            {% for r in records %}<tr><td>{{ r.enrollment_id }}</td><td>{{ r.roll_no or "Not provided" }}</td><td>{{ r.course_name }}</td>
            <td>{{ r.category }}</td><td>{{ r.enrolled_at or "Unknown" }}</td><td>{{ r.last_activity or "No activity recorded" }}</td></tr>
            {% else %}<tr><td colspan="6">No enrollments currently meet this rule.</td></tr>{% endfor %}
            </table></div></main></body></html>
        """, records=records)
    except mysql.connector.Error as error:
        return f"Inactive enrollment report error: {error}", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)
