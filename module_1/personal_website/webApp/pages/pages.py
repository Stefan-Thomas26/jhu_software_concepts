# Creating blueprint for pages so that all pages share the same template
from flask import Blueprint, render_template

bp = Blueprint("pages", __name__,
                template_folder='templates')


# A decorator used to tell the application
# the URL is assocaited function
@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/about')
def about():
    # You can render a new html template here for biography
    return "The about page"
    # return render_template('stefanThomasBiography.html')   

@bp.route('/contactInfo')
def contactInfo():
    return "Use this page to show contact info html"
    # return render_template('contactInfo.html')