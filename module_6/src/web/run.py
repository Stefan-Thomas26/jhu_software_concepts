"""
# ENTRY POINT FOR FLASK APPLICATION
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "webapp"))
import app

if __name__ == "__main__":  # pragma: no cover
    application = app.create_app()
    application.run(host="0.0.0.0", port=8080, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
