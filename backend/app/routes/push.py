"""
Module Name: Push Notifications Namespace
Description: Endpoints to manage user subscriptions for web push notifications.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from ..core import db
from ..models import PushSubscription, User

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
        """Subscribes the current user to push notifications."""
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user:
            return {"message": "Usuario no encontrado."}, 404

        data = ns.payload
        endpoint = data["endpoint"]
        keys = data["keys"]
        
        # Prevent duplicate endpoints
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
        """Removes a specific push notification subscription."""
        data = request.json
        endpoint = data.get("endpoint")
        if not endpoint:
            return {"message": "Endpoint requerido."}, 400
            
        sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()
            
        return {"message": "Suscripción eliminada."}, 200
