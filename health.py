from flask import Blueprint, render_template

health_bp = Blueprint("health", __name__)

@health_bp.route("/exercise/weightlifting", methods=["GET", "POST"])
def weightlifting():
    # Add Linear progression routines and other routines
    return render_template("weightlifting.html")


@health_bp.route("/exercise/runs", methods=["GET", "POST"]) 
def runs():
    return render_template("runs.html")


# Interval Timers merge? (Trixie Timer)
@health_bp.route("/exercise/meditation", methods=["GET", "POST"])
def meditation():
    return render_template("meditation.html")