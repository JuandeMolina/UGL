"""
Module Name: Seed Players Script
Description: Creates the 17 standard UGL players and links them to their accounts.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
    """Initializes the database with standard players."""
    from app import create_app
    from app.core import db
    from app.models import Player, User

    app = create_app()
    with app.app_context():
        existing_count = Player.query.count()
        if existing_count > 0:
            print(f"[!] Already found {existing_count} players in the database.")
            print("    Run this script only once on an empty database.")
            sys.exit(1)

        print("Creating players and linking users...\n")
        ok_count = 0
        warn_count = 0

        for name, email, is_gk in PLAYERS:
            # Create player
            player = Player(name=name, is_goalkeeper=is_gk)
            db.session.add(player)
            db.session.flush()  # Get ID before commit

            # Link user
            user = User.query.filter_by(email=email).first()
            if user:
                user.player_id = player.id
                status_icon = "✔"
                ok_count += 1
            else:
                status_icon = "⚠  (user not found, player created but not linked)"
                warn_count += 1

            gk_label = " [GK]" if is_gk else "     "
            print(f"  [{status_icon}]{gk_label} {name:<30} ← {email}")

        db.session.commit()

        print(f"\nSummary: {ok_count} linked successfully", end="")
        if warn_count:
            print(f", {warn_count} players without associated users.", end="")
        print(".")


if __name__ == "__main__":
    seed()