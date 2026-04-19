"""
Module Name: WSGI Gateway
Description: Main entry point for the combined WSGI application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.test import Client
from werkzeug.wrappers import Response

from backend.app.core import create_app as create_backend_app
from backend.config import ProductionConfig as BackendConfig
from frontend.app.core import create_app as create_frontend_app
from frontend.config import ProductionConfig as FrontendConfig

# Add project directory to path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Force production environment for internal communication logic
os.environ["FLASK_ENV"] = "production"

# Initialize applications
backend_app = create_backend_app(BackendConfig)
frontend_app = create_frontend_app(FrontendConfig)

def application(environ, start_response):
    """
    Custom WSGI router to dispatch requests between frontend and backend.
    Preserves /api, /docs, and /swaggerui for the backend.
    """
    path_info = environ.get("PATH_INFO", "")
    if path_info.startswith("/api") or path_info.startswith("/docs") or path_info.startswith("/swaggerui"):
        return backend_app(environ, start_response)
    return frontend_app(environ, start_response)

# Create a test client for internal requests
internal_client = Client(application, Response)
