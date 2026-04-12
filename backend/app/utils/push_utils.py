"""
Module Name: Push Utilities
Description: Helper functions to send web push notifications.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import json
import logging
from pywebpush import webpush, WebPushException
from flask import current_app
from ..models import PushSubscription

# VAPID Keys (Deberían estar en variables de entorno, cargamos desde config)
VAPID_CLAIMS = {
    "sub": "mailto:juande@example.com"
}

def send_push_notification(subscription, message_data):
    """Envía una notificación individual."""
    try:
        # Recuperamos claves desde la config de la app
        private_key = current_app.config.get("VAPID_PRIVATE_KEY")
        public_key = current_app.config.get("VAPID_PUBLIC_KEY")
        
        if not private_key or not public_key:
            logging.error("VAPID keys not configured.")
            return False

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=json.dumps(message_data),
            vapid_private_key=private_key,
            vapid_claims=VAPID_CLAIMS
        )
        return True
    except WebPushException as ex:
        logging.error(f"WebPush error: {ex}")
        # Si el endpoint ya no es válido, podríamos borrar la suscripción
        if ex.response and ex.response.status_code in [404, 410]:
            from ..core import db
            db.session.delete(subscription)
            db.session.commit()
        return False
    except Exception as e:
        logging.error(f"Push error: {e}")
        return False

def notify_all_users(title, body, url=None):
    """Envía una notificación a todos los usuarios suscritos."""
    subscriptions = PushSubscription.query.all()
    message = {
        "title": title,
        "body": body,
        "url": url or "/"
    }
    count = 0
    for sub in subscriptions:
        if send_push_notification(sub, message):
            count += 1
    return count
