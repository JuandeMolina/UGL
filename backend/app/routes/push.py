"""
Module Name: Push Notifications Namespace
Description: Endpoints to subscribe and unsubscribe users to push notifications.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import PushSubscription, User
from ..core import db

ns = Namespace("push", description="Notificaciones Push")

subscription_model = ns.model(
    "PushSubscription",
    {
        "endpoint": fields.String(required=True, description="Endpoint del navegador"),
        "keys": fields.Nested(ns.model("Keys", {
            "p256dh": fields.String(required=True),
            "auth": fields.String(required=True)
        }), required=True)
    }
)

@ns.route("/subscribe")
class Subscribe(Resource):
    @jwt_required()
    @ns.expect(subscription_model)
    def post(self):
        """Suscribe al usuario actual a notificaciones push."""
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            return {"message": "Usuario no encontrado."}, 404

        data = ns.payload
        endpoint = data["endpoint"]
        keys = data["keys"]
        
        # Evitar duplicados
        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            existing.user_id = user.id
            existing.p256dh = keys["p256dh"]
            existing.auth = keys["auth"]
        else:
            sub = PushSubscription(
                user_id=user.id,
                endpoint=endpoint,
                p256dh=keys["p256dh"],
                auth=keys["auth"]
            )
            db.session.add(sub)
        
        db.session.commit()
        return {"message": "Suscripción guardada con éxito."}, 201

@ns.route("/unsubscribe")
class Unsubscribe(Resource):
    @jwt_required()
    def post(self):
        """Elimina una suscripción específica."""
        data = request.json
        endpoint = data.get("endpoint")
        if not endpoint:
            return {"message": "Endpoint requerido."}, 400
            
        sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()
            
        return {"message": "Suscripción eliminada."}, 200
