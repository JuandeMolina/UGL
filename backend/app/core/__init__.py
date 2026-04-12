"""
Module Name: Core Configuration
Description:
    Creates the Flask app and initializes extensions for the UGL API server.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import logging
from pathlib import Path

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Extensions
db = SQLAlchemy()
migrate = Migrate()
api = Api(
    title="UGL API",
    version="1.0",
    description="API para la gestión de la Liga de Fútbol Sala.",
    doc="/docs",
    prefix="/api",
    authorizations={
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Escribe: Bearer <token> para autenticar",
        }
    },
)
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=None):
    """Application factory."""
    app = Flask(__name__)

    # Load config
    if config_class:
        app.config.from_object(config_class)
    else:
        import config as cfg
        app.config.from_object(cfg.Config)

    # Ensure data directory exists for SQLite
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    setup_logging(app)
    jwt.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        # Import all models so SQLAlchemy registers them before create_all
        from ..models.user import User
        from ..models.player import Player
        from ..models.match import Match
        from ..models.match_assignment import MatchAssignment
        from ..models.push_subscription import PushSubscription
        from ..models.match_confirmation import MatchConfirmation
        db.create_all()

    # Register namespaces
    from ..routes.auth import ns as auth_ns
    from ..routes.players import ns as players_ns
    from ..routes.matches import ns as matches_ns
    from ..routes.push import ns as push_ns

    api.add_namespace(auth_ns)
    api.add_namespace(players_ns)
    api.add_namespace(matches_ns)
    api.add_namespace(push_ns)
    api.init_app(app)

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({"error": "too_many_requests"}), 429

    return app


def setup_logging(app):
    if not app.debug:
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "api.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)