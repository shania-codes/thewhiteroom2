from flask import Blueprint

errors_bp = Blueprint("errors", __name__)

# Error Handling
## 404
@errors_bp.app_errorhandler(404)
def page_not_found(error):
    return '<p>404 error</p><a href="/dashboard">Back to Dashbaord</a>'

## add more