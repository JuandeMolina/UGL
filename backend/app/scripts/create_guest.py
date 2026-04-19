"""
Module Name: Create Guest Script
Description: Script to create guest accounts without a linked player.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_guest(email: str, password: str):
    """Creates a new guest user account in the database."""
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

        # Create guest user
        user = User(email=email, is_admin=False, player_id=None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"[✔] Guest account created successfully.")
        print(f"    ID:     {user.id}")
        print(f"    Email:  {user.email}")
        print(f"    Status: Guest (No player linked)")
        print(f"\n    To convert to a regular player: use 'assign_player.py'")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m app.scripts.create_guest <email> <password>")
        print("Example: python -m app.scripts.create_guest visitor@example.com MySecret123")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    password_arg = sys.argv[2]

    if not email_arg or "@" not in email_arg:
        print("[✖] Invalid email address.")
        sys.exit(1)

    if len(password_arg) < 6:
        print("[✖] Password must be at least 6 characters long.")
        sys.exit(1)

    create_guest(email_arg, password_arg)