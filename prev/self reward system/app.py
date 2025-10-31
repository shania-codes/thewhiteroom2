from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "worst_admin"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = sqlite3.connect("rewards.db")
    return db
def create_db():
    db = get_db()
    cursor = db.cursor()

    # Create tables
    ## user
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        balance INTEGER NOT NULL DEFAULT 0,
        coingoal INTEGER NOT NULL DEFAULT 0
    )
    """) 

    ## rewards
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        cost INTEGER NOT NULL DEFAULT 0,
        count INTEGER NOT NULL DEFAULT 0,
        image TEXT
    )
    """) 

    ## redeemed
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS redeemed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create initial user if there isn't one:
    cursor.execute("SELECT COUNT(*) FROM user")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        cursor.execute("INSERT INTO user (name, balance) VALUES (?, ?)", ("User", 0))

    db.commit()
    db.close()
create_db()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print(request.form)
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
                # TODO replace file name with hash of the file to support images that are the same not being duplicated and images of the same name but are different not overwriting each other

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
            cursor.execute("UPDATE user SET balance = balance + ?", (coins,))
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
                cursor.execute("UPDATE user SET balance = balance - ? WHERE id = 1", (coins,))
                
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
            cursor.execute("SELECT balance FROM user")
            balance = cursor.fetchone()[0] # User coin balance

            if balance >= cost_name[0]:
                # Deduct coins
                cursor.execute("UPDATE user SET balance = balance - ? WHERE id = 1", (cost_name[0],))
                # Log redemption
                log = str(cost_name[0]) + " coins spent - " + cost_name[1]
                cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
                cursor.execute("UPDATE rewards SET count = count + 1 WHERE id = 1")
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
            cursor.execute("UPDATE user SET coingoal = ?", (goal,))
            db.commit()
            db.close()
            flash("Coin goal updated")


    return render_template("index.html", coin_balance=get_coin_balance(), rewards=get_all_rewards(), log=get_redemption_log(), coin_goal=get_coin_goal())

@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))

# Database functions
## Get all rewards
def get_all_rewards():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM rewards ORDER BY cost DESC") # most expensive first, ASC for cheapest rewards first
    rewards = cursor.fetchall()
    db.close()
    return rewards

## Get coin balance
def get_coin_balance():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM user") 
    coin_balance = cursor.fetchone()[0]
    db.close()
    return coin_balance

## Get redemption log
def get_redemption_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM redeemed")
    log = cursor.fetchall()
    db.close()
    return log

## Get coin goal
def get_coin_goal():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT coingoal FROM user")
    goal = cursor.fetchone()[0]
    db.close()
    return goal

