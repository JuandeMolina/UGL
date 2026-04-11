"""
Module Name: Client User Model
Description:
    Lightweight User class for Flask-Login.
    No database — se construye con los datos que devuelve el API.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, email, player_id=None):
        self.id = id
        self.email = email
        self.player_id = player_id

    @staticmethod
    def from_dict(data):
        """Construye un User a partir del dict que devuelve el API."""
        return User(
            id=data["id"],
            email=data["email"],
            player_id=data.get("player_id"),
        )
