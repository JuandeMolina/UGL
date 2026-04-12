"""
Module Name: Core Configuration
Description: This module creates the app and configures extensions for the Flask client.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import logging
from pathlib import Path

from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()

API_BASE = "http://localhost:5001/api"

MONTHS_ES = {
    "01": "ene", "02": "feb", "03": "mar", "04": "abr",
    "05": "may", "06": "jun", "07": "jul", "08": "ago",
    "09": "sep", "10": "oct", "11": "nov", "12": "dic",
}


def create_app(config_class=None):
    """Application factory pattern."""
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "app" / "templates"),
        static_folder=str(BASE_DIR / "app" / "static"),
    )

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        import config
        app.config.from_object(config.Config)

    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore
    setup_logging(app)

    # Custom Jinja2 filters
    @app.template_filter("month_name")
    def month_name_filter(month_str: str) -> str:
        return MONTHS_ES.get(str(month_str).zfill(2), month_str)

    @app.template_filter("datetime_es")
    def datetime_es_filter(dt_str: str) -> str:
        """Convierte 'YYYY-MM-DD...' a 'DD/MM/YYYY'"""
        if not dt_str or len(dt_str) < 10:
            return dt_str
        try:
            date_part = dt_str[:10]
            year, month, day = date_part.split("-")
            return f"{day}/{month}/{year}"
        except:
            return dt_str

    # Register blueprints
    from ..routes.main import main
    from ..routes.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix="/auth")

    # Register error handlers
    from ..errors import register_error_handlers
    register_error_handlers(app)

    @app.context_processor
    def inject_vars():
        return dict(
            API_BASE=API_BASE,
            VAPID_PUBLIC_KEY=app.config.get("VAPID_PUBLIC_KEY")
        )

    # User loader — valida el JWT contra el API del backend
    @login_manager.user_loader
    def load_user(user_id):
        from flask import session
        import requests
        from ..models import User

        token = session.get("jwt")
        if not token:
            return None

        try:
            r = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if r.status_code != 200:
                return None
            return User.from_dict(r.json())
        except requests.RequestException:
            return None

    return app


def setup_logging(app):
    if not app.debug:
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "client.log"

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)