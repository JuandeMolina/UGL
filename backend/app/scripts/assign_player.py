"""
Module Name: Assign Player Script
Description:
    Script de línea de comandos para vincular una cuenta de usuario con su jugador.
    Uso: python -m app.scripts.assign_player <email> <player_id>
    Ejecutar desde la carpeta backend/.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def assign_player(email: str, player_id: int):
    from app import create_app
    from app.core import db
    from app.models import User, Player

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[✖] No existe ningún usuario con el correo: {email}")
            sys.exit(1)

        player = Player.query.get(player_id)
        if not player:
            print(f"[✖] No existe ningún jugador con ID: {player_id}")
            print()
            _print_players()
            sys.exit(1)

        # Comprobar que ese jugador no esté ya asignado a otro usuario
        existing = User.query.filter_by(player_id=player_id).first()
        if existing and existing.id != user.id:
            print(f"[✖] El jugador '{player.name}' ya está vinculado a: {existing.email}")
            sys.exit(1)

        user.player_id = player_id
        db.session.commit()

        print(f"[✔] Vinculación completada.")
        print(f"    Usuario:  {user.email}")
        print(f"    Jugador:  {player.name} (ID {player.id})")


def _print_players():
    """Lista todos los jugadores disponibles para facilitar la elección del ID."""
    from app import create_app
    from app.models import Player

    app = create_app()
    with app.app_context():
        players = Player.query.order_by(Player.name).all()
        if not players:
            print("  (No hay jugadores en la base de datos todavía)")
            return
        print("  Jugadores disponibles:")
        for p in players:
            gk = " [Portero]" if p.is_goalkeeper else ""
            print(f"    ID {p.id:>3} — {p.name}{gk}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Sin argumentos: mostrar lista de jugadores
        print("Uso: python -m app.scripts.assign_player <email> <player_id>")
        print("Ejemplo: python -m app.scripts.assign_player juande@liga.com 3")
        print()
        _print_players()
        sys.exit(0)

    if len(sys.argv) != 3:
        print("Uso: python -m app.scripts.assign_player <email> <player_id>")
        print("Ejemplo: python -m app.scripts.assign_player juande@liga.com 3")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    if not email_arg or "@" not in email_arg:
        print("[✖] El correo electrónico no es válido.")
        sys.exit(1)

    try:
        player_id_arg = int(sys.argv[2])
    except ValueError:
        print("[✖] El ID del jugador debe ser un número entero.")
        sys.exit(1)

    assign_player(email_arg, player_id_arg)