"""
Module Name: Main Blueprint
Description: Main page routes for the UGL client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask import Blueprint, render_template, redirect, url_for, abort, request, flash
from flask_login import login_required, current_user

from ..utils import api_get, api_post, api_put, api_delete, API_BASE

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
    r_players, _ = api_get(f"{API_BASE}/players/")
    r_matches, _ = api_get(f"{API_BASE}/matches/")

    players = r_players.json() if r_players else []
    matches = r_matches.json() if r_matches else []

    # Próximo partido (primero sin completar, en orden cronológico ascendente)
    next_match = next((m for m in reversed(matches) if not m["is_completed"]), None)

    # Las estadísticas ya vienen en el listado de jugadores (optimizado)
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

    # Identificar el nombre del jugador para el saludo
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
    if status != 200: abort(status)

    match_data = r.json()
    
    # También necesitamos los goles para la cronología
    rg, _ = api_get(f"{API_BASE}/matches/{match_id}/goals")
    goals = rg.json() if rg else []

    players = []
    if current_user.is_admin:
        rp, _ = api_get(f"{API_BASE}/players/")
        if rp: players = rp.json()

    return render_template("match_detail.html", 
                           match=match_data, 
                           goals=goals, 
                           players=players)


@main.route("/matches/<int:match_id>/assign", methods=["POST"])
@login_required
def match_assign(match_id):
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
        flash("Error al asignar jugador.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/unassign/<int:assignment_id>", methods=["POST"])
@login_required
def match_unassign(match_id, assignment_id):
    if not current_user.is_admin:
        abort(403)

    r, status = api_delete(f"{API_BASE}/matches/{match_id}/assignments/{assignment_id}")
    if status == 200:
        flash("Jugador eliminado de la plantilla.", "success")
    else:
        flash("Error al eliminar jugador.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/update_stat/<int:assignment_id>/<string:stat_type>/<string:delta>", methods=["POST"])
@login_required
def match_update_stat(match_id, assignment_id, stat_type, delta):
    delta = int(delta)
    if not current_user.is_admin:
        abort(403)

    # Obtener datos actuales del partido para encontrar la asignación
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
    if not current_user.is_admin:
        abort(403)

    data = {
        "mvp_id": request.form.get("mvp_id")
    }
    r, status = api_post(f"{API_BASE}/matches/{match_id}/complete", data)
    if status == 200:
        flash("¡Partido finalizado, marcador registrado y MVP asignado!", "success")
    else:
        flash("Error al finalizar el partido.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/matches/<int:match_id>/reopen", methods=["POST"])
@login_required
def match_reopen(match_id):
    if not current_user.is_admin:
        abort(403)

    data = {"is_completed": False}
    r, status = api_put(f"{API_BASE}/matches/{match_id}", data)
    if status == 200:
        flash("Acta reabierta. Ya puedes editar las estadísticas de nuevo.", "success")
    else:
        flash("Error al reabrir el acta.", "error")

    return redirect(url_for("main.match_detail", match_id=match_id))


@main.route("/players/<int:player_id>/edit", methods=["GET", "POST"])
@login_required
def player_edit(player_id):
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
            flash("¡Nueva jornada creada con éxito!", "success")
            return redirect(url_for("main.matches"))
        else:
            flash("Error al crear la jornada.", "error")

    return render_template("admin/match_form.html")


@main.route("/admin/matches/<int:match_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_match(match_id):
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
    if not current_user.is_admin:
        abort(403)
    
    r, status = api_get(f"{API_BASE}/auth/admin/stats")
    if status != 200 or not r:
        abort(503)
    
    stats = r.json()
    return render_template("admin/stats.html", stats=stats)

@main.route("/weird_stats")
@login_required
def weird_stats():
    r, status = api_get(f"{API_BASE}/stats/weird")
    if status == 401:
        return redirect(url_for("auth.login"))
    if status == 503 or r is None:
        abort(503)
    return render_template("stats.html", stats=r.json())