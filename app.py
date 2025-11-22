from flask import Flask#, render_template, url_for, request, redirect, flash
import os
from database import get_db, init_db
from isd import isd_bp
from food import food_bp
from health import health_bp
from management import management_bp
from errors import errors_bp

app = Flask(__name__)
app.secret_key = "worst_admin"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(isd_bp)
app.register_blueprint(food_bp)
app.register_blueprint(health_bp)
app.register_blueprint(management_bp)
app.register_blueprint(errors_bp)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Make ./static/uploads if it doesn't exist

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

init_db()