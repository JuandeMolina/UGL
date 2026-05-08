"""
Module Name: Auth Namespace
Description: Authentication endpoints for user login, identity verification, and admin stats.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, verify_jwt_in_request
from flask_restx import Namespace, Resource, fields

from ..core import db
from ..models import Match, Player, User

ns = Namespace("auth", description="Autenticación")

login_model = ns.model(
    "Login",
    {
        "email": fields.String(required=True, description="Correo electrónico"),
        "password": fields.String(required=True, description="Contraseña"),
    },
)


@ns.route("/login")
class Login(Resource):
    @ns.expect(login_model)
    def post(self):
        """Authenticates user and returns a JWT token."""
        data = ns.payload
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Credenciales incorrectas."}, 401
        
        if not user.is_active:
            return {"message": "Tu cuenta ha sido temporalmente suspendida."}, 403

        token = create_access_token(identity=str(user.id))
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "player_id": user.player_id,
                "is_admin": user.is_admin,
            },
        }, 200


@ns.route("/me")
class Me(Resource):
    @ns.doc(security="Bearer")
    def get(self):
        """Returns details of the currently authenticated user."""
        try:
            verify_jwt_in_request()
        except Exception:
            return {"message": "Token inválido o expirado."}, 401

        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return {"message": "Usuario no encontrado."}, 404

        return {
            "id": user.id,
            "email": user.email,
            "player_id": user.player_id,
            "is_admin": user.is_admin,
        }, 200


@ns.route("/admin/stats")
class AdminStats(Resource):
    @jwt_required()
    def get(self):
        """Returns system statistics (Admin only)."""
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user or not user.is_admin:
            return {"message": "Acceso denegado. Solo administradores."}, 403
        
        # User stats
        total_users = User.query.count()
        admin_count = User.query.filter_by(is_admin=True).count()
        users_with_player = User.query.filter(User.player_id.isnot(None)).count()
        
        # Match stats
        total_matches = Match.query.count()
        completed_matches = Match.query.filter_by(is_completed=True).count()
        pending_matches = total_matches - completed_matches
        
        # Player stats
        total_players = Player.query.count()
        
        # Build user list
        users_list = []
        for u in User.query.order_by(User.email).all():
            users_list.append({
                "id": u.id,
                "email": u.email,
                "is_admin": u.is_admin,
                "player_id": u.player_id,
                "player_name": u.player.name if u.player else None
            })
        
        return {
            "users": {
                "total": total_users,
                "admins": admin_count,
                "with_player": users_with_player,
                "without_player": total_users - users_with_player,
                "list": users_list
            },
            "matches": {
                "total": total_matches,
                "completed": completed_matches,
                "pending": pending_matches
            },
            "players": {
                "total": total_players
            }
        }, 200