"""
Module Name: Assign Player Script
Description: Command-line script to link a user account with a player record.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def assign_player(email: str, player_id: int):
    """Links a specific user email with a player ID."""
    from app import create_app
    from app.core import db
    from app.models import Player, User

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[✖] No user found with email: {email}")
            sys.exit(1)

        player = Player.query.get(player_id)
        if not player:
            print(f"[✖] No player found with ID: {player_id}")
            print()
            _print_players()
            sys.exit(1)

        # Ensure the player is not already linked to another user
        existing = User.query.filter_by(player_id=player_id).first()
        if existing and existing.id != user.id:
            print(f"[✖] Player '{player.name}' is already linked to: {existing.email}")
            sys.exit(1)

        user.player_id = player_id
        db.session.commit()

        print(f"[✔] Linking completed successfully.")
        print(f"    User:   {user.email}")
        print(f"    Player: {player.name} (ID {player.id})")


def _print_players():
    """Lists all available players to help identify the correct ID."""
    from app import create_app
    from app.models import Player

    app = create_app()
    with app.app_context():
        players = Player.query.order_by(Player.name).all()
        if not players:
            print("  (No players found in the database)")
            return
        print("  Available Players:")
        for p in players:
            gk_tag = " [Goalkeeper]" if p.is_goalkeeper else ""
            print(f"    ID {p.id:>3} — {p.name}{gk_tag}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments: show player list and usage
        print("Usage: python -m app.scripts.assign_player <email> <player_id>")
        print("Example: python -m app.scripts.assign_player juande@ugl.com 3")
        print()
        _print_players()
        sys.exit(0)

    if len(sys.argv) != 3:
        print("Usage: python -m app.scripts.assign_player <email> <player_id>")
        print("Example: python -m app.scripts.assign_player juande@ugl.com 3")
        sys.exit(1)

    email_arg = sys.argv[1].strip()
    if not email_arg or "@" not in email_arg:
        print("[✖] Invalid email address.")
        sys.exit(1)

    try:
        player_id_val = int(sys.argv[2])
    except ValueError:
        print("[✖] Player ID must be an integer.")
        sys.exit(1)

    assign_player(email_arg, player_id_val)