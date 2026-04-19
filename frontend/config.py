"""
Module Name: Configuration
Description: Configuration classes for the UGL client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-client")
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 365  # 1 year in seconds
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEp1ek28wEoWjKLBhxgfZ60z/+c9+yJm6xP1ltyx54TnAPqsqKgKMKXzF08C49etwsmEFA1clMwUQkbpM4c+H2jQ==")


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
