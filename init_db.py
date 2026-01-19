#!/usr/bin/env python
"""Initialize the database."""

from smspanel import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables created.")
