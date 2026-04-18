"""
Module Name: Stats API
Description: Absurd stats computation.
Author: Juande Molina
"""
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from collections import defaultdict
import itertools

from ..core import db
from ..models import Match, Goal, MatchAssignment, Player

ns = Namespace("stats", description="Estadísticas Absurdas")

def get_player_name(player_id, players_dict):
    p = players_dict.get(player_id)
    return p.name if p else "Desconocido"

@ns.route("/weird")
class WeirdStatsList(Resource):
    @jwt_required()
    def get(self):
        players = {p.id: p for p in Player.query.all()}
        matches = Match.query.filter_by(is_completed=True).all()
        assignments = MatchAssignment.query.all()
        goals = Goal.query.all()

        matches_dict = {m.id: m for m in matches}
        
        # Helper: Which team won?
        def get_winner(m):
            if m.pda_goals > m.atg_goals: return "PDA"
            if m.atg_goals > m.pda_goals: return "ATG"
            return "DRAW"

        # 1. Piedra en el zapato
        # Mejor jugador = más MVPs
        mvp_counts = defaultdict(int)
        for m in matches:
            if m.mvp_id: mvp_counts[m.mvp_id] += 1
        
        best_player_id = max(mvp_counts.keys(), key=lambda k: mvp_counts[k]) if mvp_counts else None
        piedra_en_el_zapato = None

        if best_player_id:
            # Matches of best player
            bp_assignments = [a for a in assignments if a.player_id == best_player_id]
            bp_matches = {a.match_id: a.team for a in bp_assignments}

            player_win_ratios = {}
            for a in assignments:
                if a.player_id == best_player_id: continue
                if a.match_id in bp_matches and a.team == bp_matches[a.match_id]:
                    m = matches_dict.get(a.match_id)
                    if m:
                        if a.player_id not in player_win_ratios:
                            player_win_ratios[a.player_id] = {"wins": 0, "total": 0}
                        player_win_ratios[a.player_id]["total"] += 1
                        if get_winner(m) == a.team:
                            player_win_ratios[a.player_id]["wins"] += 1
            
            # Min 3 matches with the best player
            valid_ratios = {pid: data["wins"] / data["total"] for pid, data in player_win_ratios.items() if data["total"] >= 3}
            if valid_ratios:
                worst_pid = min(valid_ratios.keys(), key=lambda k: valid_ratios[k])
                piedra_en_el_zapato = {
                    "player": get_player_name(worst_pid, players),
                    "value": f"{round(valid_ratios[worst_pid] * 100)}% ({player_win_ratios[worst_pid]['wins']}/{player_win_ratios[worst_pid]['total']})"
                }

        # 2. Amuleto del portero (Juande y José Manuel)
        # Find Juande and José Manuel
        juande = next((p for p in players.values() if "juande" in p.name.lower()), None)
        jose_manuel = next((p for p in players.values() if "josé manuel" in p.name.lower() or "jose manuel" in p.name.lower() or "jose_manuel" in p.name.lower() or "de la torre" in p.name.lower()), None)
        
        amuletos = {}
        for portero in [juande, jose_manuel]:
            if not portero: continue
            portero_assignments = {a.match_id: a.team for a in assignments if a.player_id == portero.id}
            
            player_goals_conceded = defaultdict(lambda: {"conceded": 0, "matches": 0})
            
            for a in assignments:
                if a.player_id == portero.id: continue
                if a.match_id in portero_assignments and a.team == portero_assignments[a.match_id]:
                    m = matches_dict.get(a.match_id)
                    if m:
                        conceded = m.atg_goals if a.team == "PDA" else m.pda_goals
                        player_goals_conceded[a.player_id]["conceded"] += conceded
                        player_goals_conceded[a.player_id]["matches"] += 1
            
            valid_amuletos = {pid: data["conceded"] / data["matches"] for pid, data in player_goals_conceded.items() if data["matches"] >= 3}
            if valid_amuletos:
                best_amulet_pid = min(valid_amuletos.keys(), key=lambda k: valid_amuletos[k])
                amuletos[portero.name] = {
                    "player": get_player_name(best_amulet_pid, players),
                    "value": f"{round(valid_amuletos[best_amulet_pid], 1)} goles/partido"
                }

        # 3. Minuto caliente
        minute_counts = defaultdict(int)
        for g in goals:
            minute_counts[g.minute] += 1
        minuto_caliente = max(minute_counts.keys(), key=lambda k: minute_counts[k]) if minute_counts else None
        
        # 4. Franja caliente (10 mins)
        franja_counts = defaultdict(int)
        for g in goals:
            franja_idx = g.minute // 10
            franja_counts[franja_idx] += 1
        best_franja_idx = max(franja_counts.keys(), key=lambda k: franja_counts[k]) if franja_counts else None
        franja_caliente = f"{best_franja_idx*10} - {best_franja_idx*10 + 9}" if best_franja_idx is not None else None

        # 5. Efecto siesta (Juande & José Manuel)
        efecto_siesta = {}
        for portero in [juande, jose_manuel]:
            if not portero: continue
            portero_teams = {a.match_id: a.team for a in assignments if a.player_id == portero.id}
            
            conceded_minutes = defaultdict(int)
            for g in goals:
                if g.match_id in portero_teams and g.team != portero_teams[g.match_id]:
                    conceded_minutes[g.minute] += 1
            
            if conceded_minutes:
                worst_minute = max(conceded_minutes.keys(), key=lambda k: conceded_minutes[k])
                efecto_siesta[portero.name] = {"minute": worst_minute, "count": conceded_minutes[worst_minute]}
            else:
                efecto_siesta[portero.name] = {"minute": "N/A", "count": 0}

        # 6. Rey del descuento (min >= 55)
        descuento_goals = defaultdict(int)
        for g in goals:
            if g.minute >= 55 and g.scoring_player_id:
                descuento_goals[g.scoring_player_id] += 1
        rey_descuento_pid = max(descuento_goals.keys(), key=lambda k: descuento_goals[k]) if descuento_goals else None

        # 7. Rey del inicio (min <= 5)
        inicio_goals = defaultdict(int)
        for g in goals:
            if g.minute <= 5 and g.scoring_player_id:
                inicio_goals[g.scoring_player_id] += 1
        rey_inicio_pid = max(inicio_goals.keys(), key=lambda k: inicio_goals[k]) if inicio_goals else None

        # 8. Abrelatas (1st goal of match)
        abrelatas_counts = defaultdict(int)
        goals_by_match = defaultdict(list)
        for g in goals: goals_by_match[g.match_id].append(g)
        
        for mid, m_goals in goals_by_match.items():
            if m_goals:
                first_g = min(m_goals, key=lambda x: x.created_at)
                if first_g.scoring_player_id:
                    abrelatas_counts[first_g.scoring_player_id] += 1
        abrelatas_pid = max(abrelatas_counts.keys(), key=lambda k: abrelatas_counts[k]) if abrelatas_counts else None

        # 9. Repartidor (assist different players)
        assists_targets = defaultdict(set)
        for g in goals:
            if g.assisting_player_id and g.scoring_player_id:
                assists_targets[g.assisting_player_id].add(g.scoring_player_id)
        repartidor_counts = {pid: len(targets) for pid, targets in assists_targets.items()}
        repartidor_pid = max(repartidor_counts.keys(), key=lambda k: repartidor_counts[k]) if repartidor_counts else None

        # 10. Tirador del carro (MVP losing)
        tirador_counts = defaultdict(int)
        for m in matches:
            if m.mvp_id:
                # find team of MVP
                a = next((a for a in assignments if a.match_id == m.id and a.player_id == m.mvp_id), None)
                if a:
                    winner = get_winner(m)
                    if winner != "DRAW" and winner != a.team:
                        tirador_counts[m.mvp_id] += 1
        tirador_pid = max(tirador_counts.keys(), key=lambda k: tirador_counts[k]) if tirador_counts else None

        # 11. MVP Fantasma
        top_3_mvps = sorted(mvp_counts.keys(), key=lambda k: mvp_counts[k], reverse=True)[:3]
        fantasmas = {}
        for a in assignments:
            if a.player_id not in top_3_mvps:
                if a.player_id not in fantasmas:
                    fantasmas[a.player_id] = 0
                fantasmas[a.player_id] += (a.goals + a.assists)
        fantasma_pid = max(fantasmas.keys(), key=lambda k: fantasmas[k]) if fantasmas else None

        # 12. Dupla de rendimiento (most goals assisted to each other)
        duplas_rendimiento = defaultdict(int)
        for g in goals:
            if g.scoring_player_id and g.assisting_player_id:
                pair = tuple(sorted([g.scoring_player_id, g.assisting_player_id]))
                duplas_rendimiento[pair] += 1
        best_rendimiento_pair = max(duplas_rendimiento.keys(), key=lambda k: duplas_rendimiento[k]) if duplas_rendimiento else None

        # 13. Dupla de partidos (most wins together)
        duplas_wins = defaultdict(int)
        for m in matches:
            winner = get_winner(m)
            if winner == "DRAW": continue
            # players in the winning team
            winning_players = [a.player_id for a in assignments if a.match_id == m.id and a.team == winner]
            for p1, p2 in itertools.combinations(winning_players, 2):
                pair = tuple(sorted([p1, p2]))
                duplas_wins[pair] += 1
        best_wins_pair = max(duplas_wins.keys(), key=lambda k: duplas_wins[k]) if duplas_wins else None

        # Formateo de respuesta
        result = [
            {
                "title": "Piedra en el zapato",
                "desc": "Peor porcentaje de victorias jugando con el MVP de la UGL",
                "value": piedra_en_el_zapato["player"] if piedra_en_el_zapato else "N/A",
                "subvalue": piedra_en_el_zapato["value"] if piedra_en_el_zapato else ""
            }
        ]
        
        for portero in [juande, jose_manuel]:
            if not portero: continue
            name_short = portero.name.split()[0]
            if portero.name in amuletos:
                v = amuletos[portero.name]
                result.append({
                    "title": f"Amuleto ({name_short})",
                    "desc": f"Recibe menos goles al jugar con él",
                    "value": v["player"],
                    "subvalue": v["value"]
                })
            else:
                result.append({
                    "title": f"Amuleto ({name_short})",
                    "desc": f"Recibe menos goles al jugar con él",
                    "value": "N/A",
                    "subvalue": "Faltan datos"
                })

        result.append({
            "title": "Minuto Caliente",
            "desc": "Minuto exacto con más goles registrados",
            "value": f"Minuto {minuto_caliente}" if minuto_caliente is not None else "N/A",
            "subvalue": f"{minute_counts.get(minuto_caliente, 0)} goles" if minuto_caliente is not None else ""
        })

        result.append({
            "title": "Franja Caliente",
            "desc": "Tramo de 10 minutos con más goles",
            "value": f"Minutos {franja_caliente}" if franja_caliente else "N/A",
            "subvalue": f"{franja_counts.get(best_franja_idx, 0)} goles" if franja_caliente else ""
        })

        efecto_html = ""
        for portero_name, data in efecto_siesta.items():
            name_short = portero_name.split()[0]
            efecto_html += f'<div style="margin-top:12px; display:flex; align-items:center; justify-content:space-between; background:rgba(0,0,0,0.03); padding:8px 12px; border-radius:8px;"><div style="font-size:0.9rem; font-weight:700; color:var(--text-light); text-transform:uppercase; letter-spacing:0.5px;">{name_short}</div><div style="text-align:right;"><div style="font-size:1.2rem; font-weight:800; color:var(--text-dark)">Minuto {data["minute"]}</div><div style="font-size:0.8rem; color:var(--text-mid); font-weight:600">{data["count"]} goles</div></div></div>'

        result.append({
            "title": "Efecto siesta",
            "desc": "Minuto en el que cada portero encaja estadísticamente más goles. Su talón de Aquiles temporal.",
            "value": "custom",
            "custom_html": efecto_html,
            "is_wide": True
        })

        result.append({
            "title": "Rey del descuento",
            "desc": "Más goles anotados desde el minuto 55 hasta el final del partido",
            "value": get_player_name(rey_descuento_pid, players) if rey_descuento_pid else "N/A",
            "subvalue": f"{descuento_goals.get(rey_descuento_pid, 0)} goles" if rey_descuento_pid else ""
        })

        result.append({
            "title": "Rey del inicio",
            "desc": "Más goles anotados en los primeros 5 minutos del partido",
            "value": get_player_name(rey_inicio_pid, players) if rey_inicio_pid else "N/A",
            "subvalue": f"{inicio_goals.get(rey_inicio_pid, 0)} goles" if rey_inicio_pid else ""
        })

        result.append({
            "title": "Abrelatas",
            "desc": "Jugador que más veces anota el primer gol del partido",
            "value": get_player_name(abrelatas_pid, players) if abrelatas_pid else "N/A",
            "subvalue": f"{abrelatas_counts.get(abrelatas_pid, 0)} veces" if abrelatas_pid else ""
        })

        result.append({
            "title": "Repartidor",
            "desc": "Jugador que ha asistido a más compañeros diferentes",
            "value": get_player_name(repartidor_pid, players) if repartidor_pid else "N/A",
            "subvalue": f"A {repartidor_counts.get(repartidor_pid, 0)} compañeros" if repartidor_pid else ""
        })

        result.append({
            "title": "Tirador del carro",
            "desc": "Más rondas de MVP en partidos perdidos",
            "value": get_player_name(tirador_pid, players) if tirador_pid else "N/A",
            "subvalue": f"{tirador_counts.get(tirador_pid, 0)} veces" if tirador_pid else ""
        })

        result.append({
            "title": "MVP Fantasma",
            "desc": "Mejores stats (G+A) fuera del top 3 de MVPs",
            "value": get_player_name(fantasma_pid, players) if fantasma_pid else "N/A",
            "subvalue": f"{fantasmas.get(fantasma_pid, 0)} (Goles + Asistencias)" if fantasma_pid else ""
        })

        if best_rendimiento_pair:
            p1 = get_player_name(best_rendimiento_pair[0], players)
            p2 = get_player_name(best_rendimiento_pair[1], players)
            result.append({
                "title": "Dupla de rendimiento",
                "desc": "Pareja con más goles conexionados (G+A entre ellos)",
                "value": f"{p1} & {p2}",
                "subvalue": f"{duplas_rendimiento[best_rendimiento_pair]} goles juntos"
            })
        else:
            result.append({
                "title": "Dupla de rendimiento",
                "desc": "Pareja con más goles conexionados (G+A entre ellos)",
                "value": "N/A",
                "subvalue": ""
            })

        if best_wins_pair:
            p1 = get_player_name(best_wins_pair[0], players)
            p2 = get_player_name(best_wins_pair[1], players)
            result.append({
                "title": "Dupla de partidos",
                "desc": "Pareja con más victorias jugando en el mismo equipo",
                "value": f"{p1} & {p2}",
                "subvalue": f"{duplas_wins[best_wins_pair]} victorias"
            })
        else:
            result.append({
                "title": "Dupla de partidos",
                "desc": "Pareja con más victorias jugando en el mismo equipo",
                "value": "N/A",
                "subvalue": ""
            })

        return result, 200
