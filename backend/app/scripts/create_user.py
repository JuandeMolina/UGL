"""
Module Name: Create User Script
Description: Command-line script to create user accounts.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_user(email: str, password: str, is_admin: bool = False):
    """Creates a new user account in the database."""
    from app import create_app
    from app.core import db
    from app.models import User

    app = create_app()
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"[✖] An account with this email already exists: {email}")
            return False

        # Create user
        user = User(email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"[✔] User created successfully.")
        print(f"    ID:     {user.id}")
        print(f"    Email:  {user.email}")
        print(f"    Admin:  {'Yes' if user.is_admin else 'No'}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m app.scripts.create_user <email> <password> [--admin]")
        print("Example: python -m app.scripts.create_user juande@ugl.com MySecret123 --admin")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    password_arg = sys.argv[2]
    is_admin_flag = "--admin" in sys.argv

    if not email_arg or "@" not in email_arg:
        print("[✖] Invalid email address.")
        sys.exit(1)

    if len(password_arg) < 6:
        print("[✖] Password must be at least 6 characters long.")
        sys.exit(1)

    create_user(email_arg, password_arg, is_admin_flag)
