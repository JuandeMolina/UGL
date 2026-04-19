"""
Module Name: Configuration
Description: Configuration classes for the UGL API server.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "ugl-dev-secret-key-change-this-in-production-32b")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(BASE_DIR / "data" / "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=365)
    
    # VAPID KEYS for Web Push
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEp1ek28wEoWjKLBhxgfZ60z/+c9+yJm6xP1ltyx54TnAPqsqKgKMKXzF08C49etwsmEFA1clMwUQkbpM4c+H2jQ==")
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "Pejk77SCKZNCIexIjjjZ0lhN1NfbFzFf3jUpuTAEg+ShRANCAASnV6TbzAShaMosGHGB9nrTP/5z37ImbrE/WW3LHnhOcA+qyoqAowpfMXTwLj163CyYQUDVyUzBRCRukzhz4faN")


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=365)


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=365)


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
