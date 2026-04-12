"""
Module Name: HTTP Utils
Description:
    Helper functions to communicate with the UGL API backend.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
from flask import session, redirect, url_for
import requests

API_BASE = "http://localhost:5001/api"


def _headers():
    token = session.get("jwt")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class DummyResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def _internal_request(method, url, data=None, headers=None):
    from wsgi import internal_client
    import json
    
    # Extract path from URL
    path = url.replace("http://localhost:5001", "")
    
    kwargs = {}
    if data:
        kwargs['data'] = json.dumps(data)
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'application/json'
    
    if headers:
        kwargs['headers'] = headers
        
    if method == 'GET':
        resp = internal_client.get(path, **kwargs)
    elif method == 'POST':
        resp = internal_client.post(path, **kwargs)
    elif method == 'PUT':
        resp = internal_client.put(path, **kwargs)
    elif method == 'DELETE':
        resp = internal_client.delete(path, **kwargs)
        
    # Attempt to decode JSON
    try:
        json_data = json.loads(resp.data.decode('utf-8'))
    except Exception:
        json_data = None
        
    return DummyResponse(resp.status_code, json_data)


def api_get(url, handle_401=True):
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("GET", url, headers=_headers())
        else:
            r = requests.get(url, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, 503


def api_post(url, data, handle_401=True):
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("POST", url, data=data, headers=_headers())
        else:
            r = requests.post(url, json=data, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, 503


def api_put(url, data, handle_401=True):
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("PUT", url, data=data, headers=_headers())
        else:
            r = requests.put(url, json=data, headers=_headers(), timeout=8)
            
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, 503


def api_delete(url):
    try:
        if os.environ.get("FLASK_ENV") == "production":
            r = _internal_request("DELETE", url, headers=_headers())
        else:
            r = requests.delete(url, headers=_headers(), timeout=8)
            
        return r, r.status_code
    except Exception as e:
        import traceback; traceback.print_exc()
        return None, 503

