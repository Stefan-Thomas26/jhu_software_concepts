# Creating blueprint for pages so that all pages share the same template
from flask import Blueprint, render_template

# Create blueprint; using a global 'template' folder
bp = Blueprint("pages", __name__, template_folder='templates')

# A decorator used to tell the application
# the URL is associated function

# route for home
@bp.route('/')
def home():
    return render_template('home.html')

# route for contact information
@bp.route('/contactInfo')
def contactInfo():
    return render_template('contactInfo.html')

# route for projects
@bp.route('/projects')
def projects():
    return render_template('projects.html')