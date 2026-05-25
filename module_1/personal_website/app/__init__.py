#__init__.py initializes your application creating a  flask instance


from flask import Flask, render_template

app = Flask(__name__) # Flask constructor

# A decoratore used ot tell the applicateion
# the URL is assocaited function
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    # You can render a new html template here for biography
    return "The about page"
    # return render_template('stefanThomasBiography.html')   

@app.route('/contactInfo')
def contactInfo():
    return "Use this page to show contact info html"
    # return render_template('contactInfo.html')






# Where are we running?
if __name__ == '__main__':
    # RUn the application
    app.run(host = '0.0.0.0', port = 8080)