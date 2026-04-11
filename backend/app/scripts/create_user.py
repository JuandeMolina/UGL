"""
Module Name: Create User Script
Description:
    Script de línea de comandos para crear cuentas de usuario.
    Uso: python -m app.scripts.create_user <email> <password>
    Ejecutar desde la carpeta backend/.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import sys
import os

# Añadir el directorio backend al path para poder importar la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_user(email: str, password: str):
    from app import create_app
    from app.core import db
    from app.models import User

    app = create_app()
    with app.app_context():
        # Comprobar si el usuario ya existe
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"[✖] Ya existe una cuenta con el correo: {email}")
            sys.exit(1)

        # Crear el usuario
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"[✔] Usuario creado correctamente.")
        print(f"    ID:     {user.id}")
        print(f"    Email:  {user.email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python -m app.scripts.create_user <email> <contraseña>")
        print("Ejemplo: python -m app.scripts.create_user juande@liga.com MiClave123")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    password_arg = sys.argv[2]

    if not email_arg or "@" not in email_arg:
        print("[✖] El correo electrónico no es válido.")
        sys.exit(1)

    if len(password_arg) < 6:
        print("[✖] La contraseña debe tener al menos 6 caracteres.")
        sys.exit(1)

    create_user(email_arg, password_arg)
