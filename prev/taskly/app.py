from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3


app = Flask(__name__)
app.secret_key = "worst_admin"

def get_db():
    db = sqlite3.connect("tasks.db")
    return db
def create_db():
    db = get_db()
    cursor = db.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        due_date TEXT,
        is_complete INTEGER NOT NULL DEFAULT 0,
        description TEXT
    )
    """) 

    db.commit()
    db.close()
create_db()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Add task (name, due date, description)
        if "new_task_name" in request.form:
            new_task_name = request.form["new_task_name"]
            description = request.form["description"]
            
            # SQL to add the new task to DB
            db = get_db()
            cursor = db.cursor()

            if request.form["due_date"]:
                due_date = request.form["due_date"] # yyyy-mm-dd
                cursor.execute("INSERT INTO tasks (name, due_date, description) VALUES (?, ?, ?)", (new_task_name, due_date, description,))
            else:
                cursor.execute("INSERT INTO tasks (name, description) VALUES (?, ?)", (new_task_name, description,))
            flash("Task added")
            db.commit()
            db.close()
        
        # Delete task
        if "delete_task_id" in request.form:
            delete_task_id = request.form["delete_task_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (delete_task_id,))
            flash("Task deleted")
            db.commit()
            db.close()

        # Mark task as (in)complete
        if "completed_task_id" in request.form:
            completed_task_id = request.form["completed_task_id"]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE tasks SET is_complete = 1 - is_complete WHERE id = ?", (completed_task_id,)) 
            db.commit()
            db.close()

        # Edit task
        if "edited_task_id" in request.form:
            task_id = request.form["edited_task_id"]
            new_name = request.form["edited_name"]
            new_due_date = request.form["edited_due_date"] or None
            new_description = request.form["edited_description"] or None

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE tasks SET name = ?, due_date = ?, description = ? WHERE id = ?", (new_name, new_due_date, new_description, task_id))
            flash("Task updated")
            db.commit()
            db.close()


    # db functions
    all_tasks = get_all_tasks()

    return render_template("index.html", all_tasks=all_tasks)

@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))

# Database functions
## Get all tasks
def get_all_tasks():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY due_date IS NULL, due_date ASC") # earliest due date first, DESC opposite
    tasks = cursor.fetchall()
    db.close()
    return tasks