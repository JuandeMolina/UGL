"""
Module Name: Push Subscription Model
Description: Stores web push notification subscriptions for users.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from ..core import db


class PushSubscription(db.Model):
    """Represents a web push subscription for a user."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy=True))

    def __repr__(self):
        return f"<PushSubscription {self.id} for User {self.user_id}>"
