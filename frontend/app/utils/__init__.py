"""
Module Name: HTTP Utilities
Description: Helper functions for internal/external communication between frontend and backend.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import json
import os
import traceback

import requests
from flask import session

API_BASE = "http://localhost:5001/api"


def _headers():
    """Returns authorization headers using JWT from session."""
    token = session.get("jwt")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class DummyResponse:
    """Mock requests response object for internal WSGI calls."""
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def _internal_request(method, url, data=None, headers=None):
    """
    Simulates an HTTP request to the internal WSGI backend (Monolith mode).
    """
    from wsgi import internal_client
    
    # Extract path from URL to dispatch internally
    path = url.replace("http://localhost:5001", "")
    
    kwargs = {}
    if data:
        kwargs['data'] = json.dumps(data)
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'application/json'
    
    if headers:
        kwargs['headers'] = headers
        
    # Dispatch to Werkzeug test client
    if method == 'GET':
        resp = internal_client.get(path, **kwargs)
    elif method == 'POST':
        resp = internal_client.post(path, **kwargs)
    elif method == 'PUT':
        resp = internal_client.put(path, **kwargs)
    elif method == 'DELETE':
        resp = internal_client.delete(path, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")
        
    # Decode JSON response
    try:
        json_data = json.loads(resp.data.decode('utf-8'))
    except Exception:
        json_data = None
        
    return DummyResponse(resp.status_code, json_data)


def api_get(url, handle_401=True):
    """Wrapper for GET requests to the backend API."""
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("GET", url, headers=_headers())
        else:
            r = requests.get(url, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception:
        traceback.print_exc()
        return None, 503


def api_post(url, data, handle_401=True):
    """Wrapper for POST requests to the backend API."""
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("POST", url, data=data, headers=_headers())
        else:
            r = requests.post(url, json=data, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception:
        traceback.print_exc()
        return None, 503


def api_put(url, data, handle_401=True):
    """Wrapper for PUT requests to the backend API."""
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("PUT", url, data=data, headers=_headers())
        else:
            r = requests.put(url, json=data, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception:
        traceback.print_exc()
        return None, 503


def api_delete(url):
    """Wrapper for DELETE requests to the backend API."""
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("DELETE", url, headers=_headers())
        else:
            r = requests.delete(url, headers=_headers(), timeout=8)
            
        return r, r.status_code
    except Exception:
        traceback.print_exc()
        return None, 503
