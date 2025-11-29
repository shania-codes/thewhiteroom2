from flask import Blueprint, render_template, request

health_bp = Blueprint("health", __name__)

@health_bp.route("/exercise/weightlifting", methods=["GET", "POST"])
def weightlifting():
    return render_template("weightlifting.html")


@health_bp.route("/exercise/runs", methods=["GET", "POST"]) 
def runs():
    return render_template("runs.html")


# Interval Timers merge? (Trixie Timer)
@health_bp.route("/exercise/meditation", methods=["GET", "POST"])
def meditation():

    if request.method == "POST":
        print(request.form)



    # Fake data for testing and helping me figure out schema
    sessions = [[1, "5 Minute Meditation", "Mindfulness meditation session with tibetan bells and AI TTS voice", ("Mindfulness Meditations", "AI TTS"), 300, 12], [2, "10 Minute Meditation", "Mindfulness meditation session with tibetan bells and AI TTS voice", ("Mindfulness Meditations", "AI TTS"), 600, 7], [3, "15 Minute Meditation", "Mindfulness meditation session with tibetan bells and AI TTS voice", ("Mindfulness Meditations", "AI TTS"), 900, 5]]

    max = (1, 2, 3)

    return render_template("meditation.html", sessions=sessions, max=max)