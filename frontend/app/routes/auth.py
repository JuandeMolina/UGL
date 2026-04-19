"""
Module Name: Auth Blueprint
Description: Login and logout routes for the UGL client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user

from ..models import User
from ..utils import API_BASE, api_post

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Handles user authentication requests."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            return render_template("login.html", error="Introduce tu correo y contraseña."), 400

        # Authenticate with the backend API
        r, status = api_post(
            f"{API_BASE}/auth/login",
            {"email": email, "password": password},
            handle_401=False,
        )

        if status == 429:
            abort(429)
        if status in (500, 503):
            abort(503)
        if status != 200:
            return render_template("login.html", error="Correo o contraseña incorrectos."), 401

        # Store JWT in session and log in the user locally
        data = r.json()  # type: ignore
        session["jwt"] = data["access_token"]
        session.permanent = True
        user = User.from_dict(data["user"])
        login_user(user, remember=True)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@auth.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Logs the user out and clears the session."""
    session.pop("jwt", None)
    logout_user()
    return redirect(url_for("auth.login"))
