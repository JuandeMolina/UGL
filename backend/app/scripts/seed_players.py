"""
Module Name: Seed Players Script
Description:
    Crea los 17 jugadores de la UGL y los vincula automáticamente
    a sus respectivas cuentas de usuario.
    Uso: python -m app.scripts.seed_players
    Ejecutar desde la carpeta backend/.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Nombre completo, email vinculado, es portero
PLAYERS = [
    ("Juande Molina",              "juande.molina@ugl.com",    True),
    ("José Manuel de la Torre",    "josito.torre@ugl.com",     True),
    ("Alfonso González",           "alfonso.gonzalez@ugl.com", False),
    ("Álvaro Rosales",             "alvaro.rosales@ugl.com",   False),
    ("Andrés Martínez",            "andres.martinez@ugl.com",  False),
    ("Ángel Sierra",               "angel.sierra@ugl.com",     False),
    ("Carlos Zambrana",            "carlos.zambrana@ugl.com",  False),
    ("Esteban Torres",             "esteban.torres@ugl.com",   False),
    ("Francisco Javier Rojas",     "fjavier.rojas@ugl.com",    False),
    ("Iván Berlanga",              "ivan.berlanga@ugl.com",    False),
    ("Javier Vilches",             "javier.vilches@ugl.com",   False),
    ("Jesús Moyano",               "jesus.moyano@ugl.com",     False),
    ("José Javier Gutiérrez",      "joseja.gutierrez@ugl.com", False),
    ("Juan Antonio Expósito",      "juana.exposito@ugl.com",   False),
    ("Juan Muñoz",                 "juan.munoz@ugl.com",       False),
    ("Raúl Molina",                "raul.molina@ugl.com",      False),
    ("Sergio Campos",              "sergio.campos@ugl.com",    False),
]


def seed():
    from app import create_app
    from app.core import db
    from app.models import Player, User

    app = create_app()
    with app.app_context():
        existing = Player.query.count()
        if existing > 0:
            print(f"[!] Ya existen {existing} jugadores en la base de datos.")
            print("    Ejecuta este script solo una vez, en una base de datos vacía.")
            print("    Si quieres repoblar, borra primero la tabla de jugadores.")
            sys.exit(1)

        print("Creando jugadores y vinculando usuarios...\n")
        ok = 0
        warn = 0

        for name, email, is_gk in PLAYERS:
            # Crear jugador
            player = Player(name=name, is_goalkeeper=is_gk)
            db.session.add(player)
            db.session.flush()  # Para obtener el ID antes del commit

            # Vincular usuario
            user = User.query.filter_by(email=email).first()
            if user:
                user.player_id = player.id
                status = "✔"
                ok += 1
            else:
                status = "⚠  (usuario no encontrado, jugador creado sin vincular)"
                warn += 1

            gk_label = " [P]" if is_gk else "    "
            print(f"  [{status}]{gk_label} {name:<30} ← {email}")

        db.session.commit()

        print(f"\nResumen: {ok} vinculados correctamente", end="")
        if warn:
            print(f", {warn} jugadores sin usuario asociado.", end="")
        print(".")


if __name__ == "__main__":
    seed()