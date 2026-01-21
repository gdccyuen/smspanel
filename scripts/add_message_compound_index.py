"""Migration script to add compound index on messages table."""

from flask import Flask
from smspanel import create_app
from smspanel.extensions import db

def migrate():
    app = create_app()
    with app.app_context():
        # Add compound index for existing databases
        db.session.execute(
            db.text("CREATE INDEX IF NOT EXISTS ix_messages_user_id_created_at ON messages (user_id, created_at)")
        )
        db.session.commit()
        print("Compound index added successfully")

if __name__ == "__main__":
    migrate()
