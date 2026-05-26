# run.py contains the actual python code that will import that app and start the server

from webApp import create_app

app = create_app()

# Where are we running?
if __name__ == '__main__':
    # Run the application
    app.run(host = '0.0.0.0', port = 8080, debug=True)