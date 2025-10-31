from flask import Flask, render_template, request
import sqlite3
from dateutil.rrule import rrulestr, rrule
from dateutil.parser import ParserError
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    db = sqlite3.connect("data.db")
    return db
def create_db():
    db = get_db()
    cursor = db.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        rrule TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        user_id INTEGER,
        chore_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(chore_id) REFERENCES chores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        time INTEGER  -- estimated duration in seconds (Unix-style int)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chore_steps (
        chore_id INTEGER,
        step_id INTEGER,
        FOREIGN KEY(chore_id) REFERENCES chores(id),
        FOREIGN KEY(step_id) REFERENCES steps(id)
    )
    """)

    db.commit()
    db.close()
create_db()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "add_new_user" in request.form and request.form["new_username"] != "":
            new_username = request.form["new_username"]

            # TODO: refactor this pattern is repeated in many places in code, also in TWR 
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (name) VALUES (?)", (new_username,))
            db.commit()
            db.close()

        if "delete_user" in request.form:
            delete = request.form["delete_user"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (delete,))
            db.commit()
            db.close()            

        if "add_chore" in request.form:
            name = request.form["chore_name"] # Required
            description = request.form.get("chore_desc") # Optional
            rrule = request.form.get("chore_rrule")

            # Check rrule validity TODO: Refactor, used in two places
            try:
                if rrule:
                    rrulestr(rrule)
            except Exception as e:
                return f"<p>Invalid rrule: {e}</p>"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO chores (name, description, rrule) VALUES (?, ?, ?)",(name, description, rrule))
            db.commit()
            db.close()

        if "edit_chore" in request.form:
            chore_id = request.form["chore_id"]
            name = request.form["chore_name"]
            desc = request.form["chore_desc"]
            rrule_str = request.form.get("chore_rrule", None)

            # Check rrule validity TODO: Refactor, used in two places
            try:
                if rrule_str:
                    rrulestr(rrule_str)
            except Exception as e:
                return f"<p>Invalid RRULE: {e}</p>"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE chores SET name = ?, description = ? WHERE id = ?",(name, desc, chore_id))
            db.commit()
            db.close()

        if "add_step" in request.form:
            name = request.form["step_name"]
            desc = request.form.get("step_desc")
            time = request.form.get("step_time")
            chore_id = request.form["chore_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO steps (name, description, time) VALUES (?, ?, ?)",(name, desc, time))
            step_id = cursor.lastrowid
            cursor.execute("INSERT INTO chore_steps (chore_id, step_id) VALUES (?, ?)", (chore_id, step_id))
            db.commit()
            db.close()

        if "edit_step" in request.form:
            step_id = request.form["step_id"]
            name = request.form["step_name"]
            desc = request.form["step_desc"]
            time = request.form.get("step_time")

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE steps SET name = ?, description = ?, time = ? WHERE id = ?",(name, desc, time, step_id))
            db.commit()
            db.close()

        if "delete_step" in request.form:
            step_id = request.form["delete_step"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM chore_steps WHERE step_id = ?", (step_id,))
            cursor.execute("DELETE FROM steps WHERE id = ?", (step_id,))
            db.commit()
            db.close()

        if "delete_chore" in request.form:
            chore_id = request.form["delete_chore"]

            db = get_db()
            cursor = db.cursor()

            # Clean up related records
            cursor.execute("DELETE FROM chore_steps WHERE chore_id = ?", (chore_id,))
            cursor.execute("DELETE FROM assignments WHERE chore_id = ?", (chore_id,))
            cursor.execute("DELETE FROM chores WHERE id = ?", (chore_id,))
            # Delete orphaned steps:
            cursor.execute("DELETE FROM steps WHERE id NOT IN (SELECT step_id FROM chore_steps)")

            db.commit()
            db.close()

        if "assign_user" in request.form:
            chore_id = request.form["chore_id"]
            user_id = request.form["user_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM assignments WHERE chore_id = ?", (chore_id,)) # Delete old assignment
            cursor.execute("INSERT INTO assignments (user_id, chore_id) VALUES (?, ?)", (user_id, chore_id))
            db.commit()
            db.close()


    all_chores = get_all_chores()
    chore_steps_map = {chore[0]: get_steps_for_chore(chore[0]) for chore in all_chores}
    assignments = get_chore_assignments()
    sorted_next = get_chore_next_occurrences()

    return render_template("index.html", all_users=get_all_users(), all_chores=all_chores, chore_steps_map=chore_steps_map, assignments=assignments, sorted_next=sorted_next, now=datetime.now())


@app.errorhandler(404)
def page_not_found(error):
    return "<p>404 error</p>"

# Database functions
def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    all = cursor.fetchall()
    db.close()
    return all

def get_all_chores():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM chores")
    all = cursor.fetchall()
    db.close()
    return all

def get_steps_for_chore(chore_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT steps.id, steps.name, steps.description, steps.time FROM chore_steps JOIN steps ON chore_steps.step_id = steps.id WHERE chore_steps.chore_id = ?", (chore_id,))
    results = cursor.fetchall()
    db.close()
    return results

def get_chore_assignments():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT chores.id, users.id, users.name
        FROM chores
        LEFT JOIN assignments ON chores.id = assignments.chore_id
        LEFT JOIN users ON assignments.user_id = users.id
    """)
    rows = cursor.fetchall()
    db.close()
    # returns: {chore_id: (user_id, user_name)}
    return {row[0]: (row[1], row[2]) if row[1] else (None, None) for row in rows}

def get_chore_next_occurrences():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, rrule FROM chores WHERE rrule IS NOT NULL")
    rows = cursor.fetchall()
    db.close()

    occurrences = []
    now = datetime.now()

    for chore_id, name, desc, rrule_str in rows:
        try:
            rule = rrulestr(rrule_str, dtstart=now)
            next_occurrence = rule.after(now)
            occurrences.append((next_occurrence, chore_id, name, desc))
        except Exception as e:
            occurrences.append((f"Invalid RRULE: {e}", chore_id, name, desc))

    # Sort: put datetime objects first, then strings (errors)
    def sort_key(item):
        return item[0] if isinstance(item[0], datetime) else datetime.max

    occurrences.sort(key=sort_key)

    return occurrences
