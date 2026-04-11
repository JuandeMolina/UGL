"""
Module Name: Main Blueprint
Description: Main page routes for the UGL client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required

from ..utils import api_get, API_BASE

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("auth.login"))


@main.route("/dashboard")
@login_required
def dashboard():
    r_players, _ = api_get(f"{API_BASE}/players/")
    r_matches, _ = api_get(f"{API_BASE}/matches/")

    players = r_players.json() if r_players else []
    matches = r_matches.json() if r_matches else []

    # Próximo partido (primero sin completar)
    next_match = next((m for m in reversed(matches) if not m["is_completed"]), None)

    # Estadísticas top (max goleador y asistente)
    top_scorer = None
    top_assistant = None

    return render_template(
        "dashboard.html",
        players=players,
        matches=matches,
        next_match=next_match,
        top_scorer=top_scorer,
        top_assistant=top_assistant,
    )


@main.route("/players")
@login_required
def players():
    r, status = api_get(f"{API_BASE}/players/")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("players.html", players=r.json())


@main.route("/players/<int:player_id>")
@login_required
def player_detail(player_id):
    r, status = api_get(f"{API_BASE}/players/{player_id}")
    if status == 404:
        abort(404)
    if status == 401:
        return redirect(url_for("auth.login"))
    if r is None:
        abort(503)
    return render_template("player_detail.html", player=r.json())


@main.route("/matches")
@login_required
def matches():
    r, status = api_get(f"{API_BASE}/matches/")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("matches.html", matches=r.json())


@main.route("/matches/<int:match_id>")
@login_required
def match_detail(match_id):
    r, status = api_get(f"{API_BASE}/matches/{match_id}")
    if status == 404:
        abort(404)
    if status == 401:
        return redirect(url_for("auth.login"))
    if r is None:
        abort(503)
    return render_template("match_detail.html", match=r.json())
