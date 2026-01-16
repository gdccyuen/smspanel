"""Entry point for running the Flask application."""

from ccdemo import create_app
import os

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="localhost", port=3570, debug=True)
