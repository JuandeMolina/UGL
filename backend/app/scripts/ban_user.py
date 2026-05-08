"""
Module Name: Ban User Script
Description: Command-line script to ban or unban a user.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def set_user_status(email: str, active: bool):
    """Sets the is_active status for a specific user email."""
    from app import create_app
    from app.core import db
    from app.models import User

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[✖] No user found with email: {email}")
            sys.exit(1)

        user.is_active = active
        db.session.commit()

        status = "ACTIVA" if active else "SUSPENDIDA (BANEADO)"
        print(f"[✔] Estado actualizado correctamente.")
        print(f"    Usuario: {user.email}")
        print(f"    Nuevo estado: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m app.scripts.ban_user <email> <ban|unban>")
        print("Ejemplo: python -m app.scripts.ban_user juande@ugl.com ban")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    action = sys.argv[2].lower()

    if action == "ban":
        set_user_status(email_arg, False)
    elif action == "unban":
        set_user_status(email_arg, True)
    else:
        print("[✖] Acción no reconocida. Usa 'ban' o 'unban'.")
        sys.exit(1)
