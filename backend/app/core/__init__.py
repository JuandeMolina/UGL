"""
Module Name: Core Configuration
Description: Creates the Flask app and initializes extensions for the UGL API server.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import logging
from pathlib import Path

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

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
    """
    Application factory to initialize and configure the Flask app.
    """
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        try:
            # Try relative import if part of a larger package (monolith)
            from ... import config as cfg
        except (ImportError, ValueError):
            # Fallback to absolute import if run as standalone app
            import config as cfg
        app.config.from_object(cfg.Config)

    # Ensure database directory exists
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    setup_logging(app)
    jwt.init_app(app)
    limiter.init_app(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """
        Callback to load the user from the database and verify if they are active.
        This is called on every @jwt_required request.
        """
        from ..models.user import User
        identity = jwt_data["sub"]
        user = User.query.get(int(identity))
        
        # If user doesn't exist or is not active, return None to invalidate token
        if user and not user.is_active:
            return None
            
        return user

    with app.app_context():
        # Register models
        from ..models.goal import Goal
        from ..models.match import Match
        from ..models.match_assignment import MatchAssignment
        from ..models.match_confirmation import MatchConfirmation
        from ..models.player import Player
        from ..models.award import PlayerAward
        from ..models.push_subscription import PushSubscription
        from ..models.user import User
        db.create_all()

    # Register API namespaces
    from ..routes.auth import ns as auth_ns
    from ..routes.laboratory import ns as laboratory_ns
    from ..routes.matches import ns as matches_ns
    from ..routes.players import ns as players_ns
    from ..routes.push import ns as push_ns
    from ..routes.stats import ns as stats_ns
    from ..routes.ai import ns as ai_ns

    api.namespaces.clear() # Avoid duplicates during reloads
    api.add_namespace(auth_ns)
    api.add_namespace(players_ns)
    api.add_namespace(matches_ns)
    api.add_namespace(push_ns)
    api.add_namespace(stats_ns)
    api.add_namespace(laboratory_ns)
    api.add_namespace(ai_ns)
    api.init_app(app)

    @app.errorhandler(429)
    def too_many_requests(e):
        """Global 429 Error Handler."""
        return jsonify({"error": "too_many_requests"}), 429

    return app


def setup_logging(app):
    """
    Configures log file handler for non-debug mode.
    """
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