"""
Module Name: Auth Namespace
Description:
    Authentication endpoints: login and logout.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token

from ..models import User
from ..core import db

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
        """Iniciar sesión y obtener token JWT."""
        data = ns.payload
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Credenciales incorrectas."}, 401

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
        """Devuelve los datos del usuario autenticado a partir del JWT."""
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
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

