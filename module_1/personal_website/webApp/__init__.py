#__init__.py initializes your application creating a flask instance

from flask import Flask
from webApp.pages import pages

def create_app():
     # Flask constructor
     app = Flask(__name__)
     # register blueprint defined in pages.py
     app.register_blueprint(pages.bp)

     return app