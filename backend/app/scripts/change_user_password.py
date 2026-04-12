"""
Module Name: Change Password Script
Description:
    Script de línea de comandos para cambiar la contraseña de un usuario.
    Uso: python -m app.scripts.change_user_password <email> <nueva_contraseña>
    Ejecutar desde la carpeta backend/.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def change_password(email: str, new_password: str):
    from app import create_app
    from app.core import db
    from app.models import User

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[✖] No existe ningún usuario con el correo: {email}")
            sys.exit(1)

        user.set_password(new_password)
        db.session.commit()

        print(f"[✔] Contraseña actualizada correctamente.")
        print(f"    Usuario: {user.email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python -m app.scripts.change_password <email> <nueva_contraseña>")
        print("Ejemplo: python -m app.scripts.change_password juande@liga.com NuevaClave123")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    if not email_arg or "@" not in email_arg:
        print("[✖] El correo electrónico no es válido.")
        sys.exit(1)

    password_arg = sys.argv[2]
    if len(password_arg) < 6:
        print("[✖] La contraseña debe tener al menos 6 caracteres.")
        sys.exit(1)

    change_password(email_arg, password_arg)