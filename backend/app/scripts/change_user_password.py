"""
Module Name: Change Password Script
Description: Command-line script to update a user's password.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def change_password(email: str, new_password: str):
    """Updates the password for a specific user email."""
    from app import create_app
    from app.core import db
    from app.models import User

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[✖] No user found with email: {email}")
            sys.exit(1)

        user.set_password(new_password)
        db.session.commit()

        print(f"[✔] Password updated successfully.")
        print(f"    User: {user.email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.scripts.change_user_password <email> <new_password>")
        print("Example: python -m app.scripts.change_user_password juande@ugl.com NewSecret123")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    if not email_arg or "@" not in email_arg:
        print("[✖] Invalid email address.")
        sys.exit(1)

    password_arg = sys.argv[2]
    if len(password_arg) < 6:
        print("[✖] Password must be at least 6 characters long.")
        sys.exit(1)

    change_password(email_arg, password_arg)