# run.py contains the actual python code that will import that app and start the server

from webApp import create_app

app = create_app()

# run the app with run.py is called from command line
if __name__ == '__main__':
    # Run the application at port 8080 and local host 0.0.0.0
    app.run(host = '0.0.0.0', port = 8080, debug=True)