# Creating blueprint for pages so that all pages share the same template
from flask import Blueprint, render_template

bp = Blueprint("pages", __name__, template_folder='templates')


# A decorator used to tell the application
# the URL is assocaited function
@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/contactInfo')
def contactInfo():
    return render_template('contactInfo.html')

@bp.route('/projects')
def projects():
    return render_template('projects.html')