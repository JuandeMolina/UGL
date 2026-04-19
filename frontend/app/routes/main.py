"""
Module Name: Main Blueprint
Description: Main page routes for the UGL client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..utils import API_BASE, api_delete, api_get, api_post, api_put

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("auth.login"))


@main.route("/sw.js")
def service_worker():
    from flask import current_app, send_from_directory
    return send_from_directory(current_app.static_folder, "sw.js")


@main.route("/dashboard")
@login_required
def dashboard():
    """Renders the user dashboard with player stats and upcoming matches."""
    r_players, _ = api_get(f"{API_BASE}/players/")
    r_matches, _ = api_get(f"{API_BASE}/matches/")

    players = r_players.json() if r_players else []
    matches = r_matches.json() if r_matches else []

    # Next match (first uncompleted, ascending chronological order)
    next_match = next((m for m in reversed(matches) if not m["is_completed"]), None)

    # Statistics are included in the player list (optimized)
    player_stats = []
    for p in players:
        stats = p.get("stats", {"goals": 0, "assists": 0, "wins": 0})
        player_stats.append({
            "id": p["id"],
            "name": p["name"],
            "goals": stats["goals"],
            "assists": stats["assists"],
            "wins": stats["wins"],
        })

    def build_top(stat_key, n=5):
        ranked = sorted(player_stats, key=lambda x: x[stat_key], reverse=True)
        return [(i + 1, p) for i, p in enumerate(ranked[:n]) if p[stat_key] > 0]

    top_scorers = build_top("goals")
    top_assisters = build_top("assists")
    top_winners = build_top("wins")

    # Identify player name for greeting
    display_name = current_user.email.split('@')[0]
    if current_user.player_id:
        curr_player = next((p for p in players if p['id'] == current_user.player_id), None)
        if curr_player:
            name_parts = curr_player['name'].split()
            if len(name_parts) > 1:
                display_name = " ".join(name_parts[:-1])
            else:
                display_name = curr_player['name']

    return render_template(
        "dashboard.html",
        players=players,
        matches=matches,
        next_match=next_match,
        top_scorers=top_scorers,
        top_assisters=top_assisters,
        top_winners=top_winners,
        display_name=display_name
    )


@main.route("/players")
@login_required
def players():
    """Renders the player list."""
    r, status = api_get(f"{API_BASE}/players/")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("players.html", players=r.json())


@main.route("/players/<int:player_id>")
@login_required
def player_detail(player_id):
    """Renders a specific player's profile."""
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
    """Renders the match list."""
    r, status = api_get(f"{API_BASE}/matches/")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("matches.html", matches=r.json())


@main.route("/matches/<int:match_id>")
@login_required
def match_detail(match_id):
    """Renders details for a specific match, including timeline and lineups."""
    r, status = api_get(f"{API_BASE}/matches/{match_id}")
    if status != 200: abort(status)

    match_data = r.json()
    
    # We also need goals for the timeline
    rg, _ = api_get(f"{API_BASE}/matches/{match_id}/goals")
    goals = rg.json() if rg else []

    players_list = []
    if current_user.is_admin:
        rp, _ = api_get(f"{API_BASE}/players/")
        if rp: players_list = rp.json()

    return render_template("match_detail.html", 
                           match=match_data, 
                           goals=goals, 
                           players=players_list)


@main.route("/matches/<int:match_id>/assign", methods=["POST"])
@login_required
def match_assign(match_id):
    """Assigns a player to a specific team in a match (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    data = {
        "player_id": int(request.form.get("player_id")),
        "team": request.form.get("team")
    }
    r, status = api_post(f"{API_BASE}/matches/{match_id}/assignments", data)
    if status == 201:
        flash("Jugador asignado correctamente.", "success")
    else:
        flash("Error al asignar el jugador.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/unassign/<int:assignment_id>", methods=["POST"])
@login_required
def match_unassign(match_id, assignment_id):
    """Removes a player from a match team (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    r, status = api_delete(f"{API_BASE}/matches/{match_id}/assignments/{assignment_id}")
    if status == 200:
        flash("Jugador eliminado de la convocatoria.", "success")
    else:
        flash("Error al eliminar el jugador.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/update_stat/<int:assignment_id>/<string:stat_type>/<string:delta>", methods=["POST"])
@login_required
def match_update_stat(match_id, assignment_id, stat_type, delta):
    """Updates individual player stats during a match (Admin only)."""
    delta = int(delta)
    if not current_user.is_admin:
        abort(403)

    # Get current match data to find the assignment
    r, _ = api_get(f"{API_BASE}/matches/{match_id}")
    if not r:
        return redirect(url_for("main.match_detail", match_id=match_id))
    
    match_data = r.json()
    assignment = next((a for a in match_data["assignments"] if a["id"] == assignment_id), None)
    
    if assignment:
        new_val = max(0, assignment[stat_type] + delta)
        data = {stat_type: new_val}
        api_put(f"{API_BASE}/matches/{match_id}/assignments/{assignment_id}", data)

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/complete", methods=["POST"])
@login_required
def match_complete(match_id):
    """Finalizes a match and assigns the MVP (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    data = {
        "mvp_id": request.form.get("mvp_id")
    }
    r, status = api_post(f"{API_BASE}/matches/{match_id}/complete", data)
    if status == 200:
        flash("¡Partido finalizado, estadísticas registradas y MVP asignado!", "success")
    else:
        flash("Error al finalizar el partido.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/reopen", methods=["POST"])
@login_required
def match_reopen(match_id):
    """Reopens a finalized match for stat editing (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    data = {"is_completed": False}
    r, status = api_put(f"{API_BASE}/matches/{match_id}", data)
    if status == 200:
        flash("Convocatoria reabierta. Ya puedes editar estadísticas de nuevo.", "success")
    else:
        flash("Error al reabrir la convocatoria.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/players/<int:player_id>/edit", methods=["GET", "POST"])
@login_required
def player_edit(player_id):
    """Edits a player's profile information (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        data = {
            "jersey_number": int(request.form.get("jersey_number")) if request.form.get("jersey_number") else None,
            "photo_url": request.form.get("photo_url") or None,
            "description": request.form.get("description") or None,
        }
        r, status = api_put(f"{API_BASE}/players/{player_id}", data)
        if status == 200:
            flash("Perfil actualizado correctamente.", "success")
            return redirect(url_for("main.player_detail", player_id=player_id))
        else:
            flash("Error al actualizar el perfil.", "error")

    r, status = api_get(f"{API_BASE}/players/{player_id}")
    if status != 200:
        abort(status)
        
    return render_template("admin/player_edit.html", player=r.json())


@main.route("/admin/matches/new", methods=["GET", "POST"])
@login_required
def admin_new_match():
    """Creates a new match session (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        data = {
            "matchday": int(request.form.get("matchday")),
            "date": request.form.get("date"),
            "location": request.form.get("location"),
            "cost": float(request.form.get("cost")),
            "pda_kit_color": request.form.get("pda_kit_color"),
            "atg_kit_color": request.form.get("atg_kit_color")
        }
        r, status = api_post(f"{API_BASE}/matches/", data)
        if status == 201:
            flash("¡Nueva jornada creada correctamente!", "success")
            return redirect(url_for("main.matches"))
        else:
            flash("Error al crear el partido.", "error")

    return render_template("admin/match_form.html")


@main.route("/admin/matches/<int:match_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_match(match_id):
    """Edits basic match session settings (Admin only)."""
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        data = {
            "matchday": int(request.form.get("matchday")),
            "date": request.form.get("date"),
            "location": request.form.get("location"),
            "cost": float(request.form.get("cost")),
            "pda_kit_color": request.form.get("pda_kit_color"),
            "atg_kit_color": request.form.get("atg_kit_color"),
            "playing_now": "playing_now" in request.form
        }
        r, status = api_put(f"{API_BASE}/matches/{match_id}", data)
        if status == 200:
            flash("Partido actualizado correctamente.", "success")
            return redirect(url_for("main.match_detail", match_id=match_id))
        else:
            flash("Error al actualizar el partido.", "error")

    r, status = api_get(f"{API_BASE}/matches/{match_id}")
    if status != 200:
        abort(404)
    
    return render_template("admin/match_edit.html", match=r.json())


@main.route("/admin/stats")
@login_required
def admin_stats():
    """Renders administrative database stats (Admin only)."""
    if not current_user.is_admin:
        abort(403)
    
    r, status = api_get(f"{API_BASE}/auth/admin/stats")
    if status != 200 or not r:
        abort(503)
    
    stats_data = r.json()
    return render_template("admin/stats.html", stats=stats_data)


@main.route("/weird_stats")
@login_required
def weird_stats():
    """Renders the absurd stats dashboard."""
    r, status = api_get(f"{API_BASE}/stats/weird")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("stats.html", stats=r.json())


@main.route("/laboratory")
@login_required
def laboratory():
    """Renders the advanced stats laboratory."""
    r, status = api_get(f"{API_BASE}/players/")
    if status != 200:
        abort(503)
    players_data = sorted(r.json(), key=lambda x: x["name"])
    return render_template("laboratory.html", players=players_data)