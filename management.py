from flask import Blueprint, render_template, request, url_for, flash, redirect
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from dateutil.rrule import rrulestr
from database_functions import *

management_bp = Blueprint("management", __name__)


@management_bp.route("/routes", methods=["GET", "POST"])
def routes():
    if request.method == "POST":
        print(request.form)
        # Create route and root node
        if "newRoute" in request.form:
            route_name = request.form["newRouteName"]
            route_description = request.form.get("newRouteDescription") or None

            db = get_db()
            cursor = db.cursor()

            # Create route
            cursor.execute("INSERT INTO routes (name, description) VALUES (?, ?)", (route_name, route_description))

            route_id = cursor.lastrowid

            # Create root node
            cursor.execute("INSERT INTO nodes (name, content, type, status, route_id) VALUES (?, ?, ?, ?, ?)", (route_name, route_description, "root", "not_started", route_id),)

            db.commit()
            db.close()
            flash("Route created.")
            return redirect("/routes")

        # Add child nodes to route tree
        if "newRouteNode" in request.form:
            route_id = request.form["route_id"]
            step_name = request.form["stepName"]
            step_type = request.form["stepType"]
            step_content = request.form["stepContent"]

            db = get_db()
            cursor = db.cursor()

            cursor.execute("INSERT INTO nodes (name, content, type, status, route_id) VALUES (?, ?, ?, ?, ?)", (step_name, step_content, step_type, "not_started", route_id))

            db.commit()
            db.close()
            flash("Step added.")
            return redirect("/routes")
            
            
    #

    return render_template("routes.html", routes=get_all_routes())


@management_bp.route("/tasks", methods=["GET", "POST"])
def tasks():
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
            cursor.execute("UPDATE tasks SET is_complete = 1 - is_complete WHERE id = ?", (completed_task_id,)) # Maths W
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

    return render_template("tasks.html", all_tasks=get_all_tasks())


@management_bp.route("/rewards", methods=["GET", "POST"])
def rewards():
    if request.method == "POST":
        # Add reward (name, description, coins)
        if "new_reward_name" in request.form:
            new_reward_name = request.form["new_reward_name"]
            description = request.form["description"]
            cost = request.form["coins"]

            db = get_db()
            cursor = db.cursor()
            
            file = request.files["image"]
            if file.filename == "": # if no file is uploaded
                filename = None 
            elif file and allowed_file(file.filename): # If the file exists and it has an allowed name and file extension then save it
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # TODO replace file name with hash of the file to support images that are the same but with different file names, not being stored twice. Furthermore images of the same name but are different not overwriting each other.

            cursor.execute("INSERT INTO rewards (name, description, cost, image) VALUES (?, ?, ?, ?)", (new_reward_name, description, cost, filename))
            
            flash("Reward added")
            db.commit()
            db.close()

        # Edit reward
        if "edited_reward" in request.form:
            edited = request.form["edited_reward"]
            new_reward_name = request.form["reward_name"]
            new_description = request.form["description"]
            new_cost = request.form["coins"]
            
            db = get_db()
            cursor = db.cursor()

            file = request.files["image"]
            if file.filename == "": # if no new file is uploaded
                cursor.execute("UPDATE rewards SET name = ?, description = ?, cost = ? WHERE id = ?", (new_reward_name, new_description, new_cost, edited))
            elif file and allowed_file(file.filename): # If a new file is uploaded
                # delete old file
                cursor.execute("SELECT image FROM rewards WHERE id = ?", (edited,))
                old_file = cursor.fetchone()[0]
                if old_file:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # upload new file
                cursor.execute("UPDATE rewards SET name = ?, description = ?, cost = ?, image = ? WHERE id = ?", (new_reward_name, new_description, new_cost, filename, edited)) # Update DB with new file

            flash("Reward updated")
            db.commit()
            db.close()
        
        # Delete reward
        if "delete_reward" in request.form:
            delete = request.form["reward_id"]

            db = get_db()
            cursor = db.cursor()

            # delete old file
            cursor.execute("SELECT image FROM rewards WHERE id = ?", (delete,))
            old_file = cursor.fetchone()[0]
            if old_file:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)

            cursor.execute("DELETE FROM rewards WHERE id = ?", (delete,))

            flash("Reward deleted")
            db.commit()
            db.close()

        # Add coins
        if request.form.get("action") == "add":
            coins = request.form["coins"]
            reason = request.form.get("reason") or "No reason given"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE reward_user SET balance = balance + ?", (coins,))
            log = coins + " coins added - " + reason
            cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
            db.commit()
            db.close()
            flash("Added coins")

        # Subtract coins
        if request.form.get("action") == "subtract":
            coins = int(request.form["coins"])
            reason = request.form.get("reason") or "No reason given"
            balance = int(get_coin_balance())

            db = get_db()
            cursor = db.cursor()

            if balance >= coins: # in this case balance - coins can't be negative only 0 or more
                cursor.execute("UPDATE reward_user SET balance = balance - ? WHERE id = 1", (coins,))
                
                log = f"{coins} coins removed - {reason}"
                cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
                
                db.commit()
                db.close()
                flash("Subtracted coins") 
            else:
                flash("Not enough coins in balance")

        # Redeem reward
        if "redeemed_id" in request.form:
            reward_id = request.form["redeemed_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT cost, name FROM rewards WHERE id = ?", (reward_id,))
            cost_name = cursor.fetchone() # Reward cost, reward name
            cursor.execute("SELECT balance FROM reward_user")
            balance = cursor.fetchone()[0] # User coin balance

            if balance >= cost_name[0]:
                # Deduct coins
                cursor.execute("UPDATE reward_user SET balance = balance - ? WHERE id = 1", (cost_name[0],))
                # Log redemption
                log = str(cost_name[0]) + " coins spent - " + cost_name[1]
                cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
                cursor.execute("UPDATE rewards SET count = count + 1 WHERE id = ?", (reward_id,))
                db.commit()
                flash("Reward redeemed!")
            else:
                flash("Not enough coins to redeem this reward.")
            db.close()

        # Delete redeem log entry
        if "entry_id" in request.form:
            entry_id = request.form["entry_id"]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM redeemed WHERE id = ?", (entry_id,))
            db.commit()
            db.close()
            flash("Deleted redeem log entry")

        # Redeem log clear
        if "redeem" in request.form:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM redeemed")
            db.commit()
            db.close()
            flash("Redemption log cleared")

        # Set coin goal
        if "coin_goal" in request.form:
            goal = request.form["coin_goal"]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE reward_user SET coingoal = ?", (goal,))
            db.commit()
            db.close()
            flash("Coin goal updated")

    return render_template("rewards.html", coin_balance=get_coin_balance(), rewards=get_all_rewards(), log=get_redemption_log(), coin_goal=get_coin_goal())


@management_bp.route("/timers")
def timers(): # TODO rewrite it but make it better, merge with meditation timers?
    return render_template("timers.html")


@management_bp.route("/chores", methods=["GET", "POST"])
def chores():
    if request.method == "POST":
        if "add_new_user" in request.form and request.form["new_username"] != "":
            new_username = request.form["new_username"]

            # TODO: refactor this pattern is repeated in many places in code, also in TWR 
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO chore_users (name) VALUES (?)", (new_username,))
            db.commit()
            db.close()

        if "delete_user" in request.form:
            delete = request.form["delete_user"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM chore_users WHERE id = ?", (delete,))
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

    return render_template("chores.html", all_users=get_all_users(), all_chores=all_chores, chore_steps_map=chore_steps_map, assignments=assignments, sorted_next=sorted_next, now=datetime.now())
