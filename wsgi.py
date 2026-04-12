import os
import sys

# Add the project directory to the path so modules are found
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Force production environment to trigger internal requests
os.environ["FLASK_ENV"] = "production"

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from backend.app.core import create_app as create_backend_app
from frontend.app.core import create_app as create_frontend_app
from backend.config import ProductionConfig as BackendConfig
from frontend.config import ProductionConfig as FrontendConfig

# Create both applications with production configs
backend_app = create_backend_app(BackendConfig)
frontend_app = create_frontend_app(FrontendConfig)

# The backend uses paths starting with /api (Api(prefix='/api')).
# We construct a custom WSGI router to preserve the prefix.
def application(environ, start_response):
    if environ.get("PATH_INFO", "").startswith("/api") or environ.get("PATH_INFO", "").startswith("/docs") or environ.get("PATH_INFO", "").startswith("/swaggerui"):
        return backend_app(environ, start_response)
    return frontend_app(environ, start_response)

# Create a test client of the combined application for internal requests
from werkzeug.test import Client
from werkzeug.wrappers import Response
internal_client = Client(application, Response)
