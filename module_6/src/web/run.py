import os
from app import app as flask_app

# ===========
# ENTRY POINT
# ===========
if __name__ == "__main__":  # pragma: no cover
    application = flask_app.create_app()
    application.run(host="0.0.0.0", port=8080, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
