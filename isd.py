from flask import Blueprint, render_template, redirect, url_for, request, flash
from database import get_db

isd_bp = Blueprint("isd", __name__)

@isd_bp.route("/")
def index():  
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata LIMIT 1")
    result = cursor.fetchone()
    db.close()
    # Check if name exists and is not empty
    if result and result[0].strip():
        return redirect(url_for("isd.dashboard"))
    else:
        return redirect(url_for("isd.setup"))
    

@isd_bp.route("/setup", methods=["GET", "POST"])
def setup():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata LIMIT 1")
    result = cursor.fetchone()

    if result:
        db.close()
        return redirect(url_for("isd.dashboard")) # Redirect to dashboard if username exists

    if request.method == "POST":
        # Get inputs from form and save them to variables
        name = request.form.get("name").strip()
        weightGoal = request.form.get("weightGoal")
        currentWeight = request.form.get("currentWeight")
        calorieTarget = request.form.get("calorieTarget")
        proteinTarget = request.form.get("proteinTarget")
        carbsTarget = request.form.get("carbsTarget")
        fatTarget = request.form.get("fatTarget")
        waterTarget = request.form.get("waterTarget")
        allergies = request.form.get("allergies").strip()
        dietaryPreferences = request.form.get("dietaryPreferences").strip()

        if name != "":
            # Save the value to the userdata table
            cursor.execute("""
                INSERT INTO userdata (
                    name, weightGoal, currentWeight, calorieTarget,
                    proteinTarget, carbsTarget, fatTarget, waterTarget,
                    allergies, dietaryPreferences) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (name, weightGoal, currentWeight, calorieTarget,proteinTarget, carbsTarget, fatTarget, waterTarget, allergies, dietaryPreferences))
            db.commit() # Save
            db.close()
            return redirect(url_for("isd.dashboard"))
        else:
            flash("Please input a username")
            return redirect(url_for("isd.setup"))

    return render_template("setup.html")


@isd_bp.route("/dashboard")
def dashboard():
    # Get name from the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata")
    result = cursor.fetchone()
    if result:
        name = result[0]
        return render_template("dashboard.html", name=name)

    return redirect(url_for("isd.setup"))


@isd_bp.route("/settings", methods=["GET", "POST"])
def settings():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST": #When submit button is pressed
        # Get inputs from form and save them to variables
        name = request.form.get("name").strip()
        weightGoal = request.form.get("weightGoal")
        currentWeight = request.form.get("currentWeight")
        calorieTarget = request.form.get("calorieTarget")
        proteinTarget = request.form.get("proteinTarget")
        carbsTarget = request.form.get("carbsTarget")
        fatTarget = request.form.get("fatTarget")
        waterTarget = request.form.get("waterTarget")
        allergies = request.form.get("allergies")
        dietaryPreferences = request.form.get("dietaryPreferences")

        cursor.execute("""
            UPDATE userdata SET
                name = ?,
                weightGoal = ?,
                currentWeight = ?,
                calorieTarget = ?,
                proteinTarget = ?,
                carbsTarget = ?,
                fatTarget = ?,
                waterTarget = ?,
                allergies = ?,
                dietaryPreferences = ?""", 
                (name, weightGoal, currentWeight, calorieTarget, proteinTarget, carbsTarget, fatTarget, waterTarget, allergies, dietaryPreferences))
        db.commit()
        return redirect(url_for("isd.dashboard"))

    cursor.execute("SELECT * FROM userdata")
    userdata = cursor.fetchone()
    return render_template("settings.html", userdata=userdata)