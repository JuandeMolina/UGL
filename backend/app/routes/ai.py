import json
import re
import logging
from collections import defaultdict
import itertools

from flask import request, current_app
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from google import genai

from ..models import Player, Match, MatchAssignment, Goal, MatchConfirmation
from ..core import db

ns = Namespace("ai", description="Sugerencias por Inteligencia Artificial")

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

def get_player_full_context(player_ids):
    players = Player.query.filter(Player.id.in_(player_ids)).all()
    all_assignments = MatchAssignment.query.all()
    all_goals = Goal.query.all()
    
    context = []
    for p in players:
        p_assignments = [a for a in all_assignments if a.player_id == p.id]
        wins = 0
        for a in p_assignments:
            m = Match.query.get(a.match_id)
            if m and m.is_completed:
                winner = "PDA" if m.pda_goals > m.atg_goals else "ATG"
                if winner == a.team: wins += 1
        
        affinities = {}
        p_goals = [g for g in all_goals if g.scoring_player_id == p.id or g.assisting_player_id == p.id]
        for g in p_goals:
            other = g.assisting_player_id if g.scoring_player_id == p.id else g.scoring_player_id
            if other and other != p.id:
                affinities[other] = affinities.get(other, 0) + 1

        context.append({
            "id": p.id,
            "name": p.name,
            "level_hint": p.description or "Nivel medio",
            "is_goalkeeper": p.is_goalkeeper,
            "win_rate": f"{round((wins/len(p_assignments)*100), 1) if p_assignments else 0}%",
            "goals_total": sum(a.goals for a in p_assignments),
            "assists_total": sum(a.assists for a in p_assignments),
            "affinities": affinities 
        })
    return context

def get_rotation_data(player_ids):
    all_completed_matches = Match.query.filter_by(is_completed=True).all()
    history_matrix = defaultdict(int)
    for m in all_completed_matches:
        pda_ids = [a.player_id for a in m.assignments if a.team == "PDA" and a.player_id in player_ids]
        atg_ids = [a.player_id for a in m.assignments if a.team == "ATG" and a.player_id in player_ids]
        for p1, p2 in itertools.combinations(pda_ids, 2):
            pair = tuple(sorted((p1, p2)))
            history_matrix[pair] += 1
        for p1, p2 in itertools.combinations(atg_ids, 2):
            pair = tuple(sorted((p1, p2)))
            history_matrix[pair] += 1
    return {f"{k[0]}-{k[1]}": v for k, v in history_matrix.items()}

@ns.route("/suggest-teams/<int:match_id>")
class AISuggestion(Resource):
    @jwt_required()
    def get(self, match_id):
        try:
            confirmations = MatchConfirmation.query.filter_by(match_id=match_id, will_attend=True).all()
            player_ids = [c.player_id for c in confirmations]
            
            if not player_ids:
                return {"message": "No hay jugadores confirmados."}, 400

            players_data = get_player_full_context(player_ids)
            rotation_history = get_rotation_data(player_ids)
            api_key = current_app.config.get("GEMINI_API_KEY")
            
            client = genai.Client(api_key=api_key)
            
            # --- DETECCIÓN AUTOMÁTICA DE MODELO ---
            # Listamos modelos y buscamos el Flash más reciente disponible
            available_models = [m.name for m in client.models.list()]
            # Buscamos 'gemini-2.0-flash', 'gemini-1.5-flash', etc.
            flash_models = [name for name in available_models if 'flash' in name.lower()]
            
            if not flash_models:
                return {"error": f"No se encontraron modelos Flash. Disponibles: {available_models}"}, 500
            
            # Elegimos el primero de la lista (suele ser el más nuevo o el principal)
            target_model = flash_models[0] 
            logging.info(f"Usando modelo detectado: {target_model}")

            prompt = f"""
            Actúa como entrenador de fútbol sala para la liga UGL. Equilibra PDA y ATG.
            DATOS JUGADORES: {json.dumps(players_data)}
            ROTACIÓN: {json.dumps(rotation_history)}
            REGLAS:
            - Portero PDA: ID 1. Portero ATG: ID 2.
            - Si es impar ({len(player_ids)}), el equipo con menos jugadores debe ser mejor técnicamente.
            - Evitar juntar parejas con historial >= 3.
            RESPONDE EXCLUSIVAMENTE EN JSON:
            {{ "pda": [ids], "atg": [ids], "justification": "..." }}
            """

            response = client.models.generate_content(
                model=target_model,
                contents=prompt
            )
            
            suggestion = json.loads(extract_json(response.text))
            
            names_map = {p["id"]: p["name"] for p in players_data}
            suggestion["pda_names"] = [names_map.get(pid, f"ID {pid}") for pid in suggestion["pda"]]
            suggestion["atg_names"] = [names_map.get(pid, f"ID {pid}") for pid in suggestion["atg"]]
            
            return suggestion, 200

        except Exception as e:
            logging.error(f"Error IA: {str(e)}")
            return {"error": str(e)}, 500