"""
Module Name: HTTP Utils
Description:
    Helper functions to communicate with the UGL API backend.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import session, redirect, url_for
import requests

API_BASE = "http://localhost:5001/api"


def _headers():
    token = session.get("jwt")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(url, handle_401=True):
    try:
        r = requests.get(url, headers=_headers(), timeout=8)
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except requests.RequestException:
        return None, 503


def api_post(url, data, handle_401=True):
    try:
        r = requests.post(url, json=data, headers=_headers(), timeout=8)
        if handle_401 and r.status_code == 401:
            return None, 401
        return r, r.status_code
    except requests.RequestException:
        return None, 503


def api_delete(url):
    try:
        r = requests.delete(url, headers=_headers(), timeout=8)
        return r, r.status_code
    except requests.RequestException:
        return None, 503
