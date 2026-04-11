1. Contexto del Proyecto
El objetivo es crear una aplicación web con Flask para gestionar una liga de fútbol sala privada (18 jugadores). El sistema debe permitir el acceso restringido mediante inicio de sesión para que los amigos puedan consultar estadísticas y partidos. Los equipos (Plantilla A y Plantilla B) tienen nombres, escudos y porteros fijos, pero los jugadores de campo rotan en cada jornada.

2. Requisitos Técnicos
Framework: Flask (Python).

Base de Datos: SQLite (suficiente para < 20 usuarios).

ORM: SQLAlchemy.

Frontend: HTML/Jinja2 + CSS (archivo en frontend/static/style.css reciclado de otro proyecto).

3. Modelo de Datos (Esquema Sugerido)
User: id, email (unique), password_hash, player_id (relación 1:1 opcional si el usuario es también jugador).

Player: id, name, is_goalkeeper (bool), photo_url.

Match: id, date, team_a_goals, team_b_goals, is_completed (bool).

MatchAssignment: match_id, player_id, team (A o B), goals, assists.

Nota: Esta tabla es vital para rastrear en qué equipo jugó cada persona en cada partido específico.

4. Funcionalidades y Pantallas
Autenticación
Login: Pantalla de acceso con correo electrónico y contraseña.

Protección de Rutas: Todas las pantallas (Inicio, Partidos, Jugadores) deben requerir que el usuario esté autenticado (@login_required).

Pantalla de Inicio (Dashboard)
Resumen del Próximo Partido.

Estadísticas destacadas (Máximo goleador y Máximo asistente).

Pantalla de Partidos
Listado cronológico descendente.

Detalle de Partido: Visualización persistente de los equipos configurados para esa jornada específica y el desglose de goles/asistencias.

Pantalla de Jugadores
Listado de los 18 integrantes.

Perfil Individual: Estadísticas totales (Goles, Asistencias, Partidos) y cálculos derivados (Victorias/Derrotas según el equipo asignado en cada jornada).

5. Lógica de Negocio y Seguridad
Persistencia Histórica: La asignación de jugadores a un equipo en un partido debe quedar grabada en MatchAssignment para que los cambios en jornadas futuras no alteren el historial.

Cálculo de Resultados: Las victorias de un jugador se computan si su equipo en ese partido marcó más goles que el rival.

Seguridad: Las contraseñas nunca deben almacenarse en texto plano; usar generate_password_hash.

6. Instrucciones de Implementación
Configurar el LoginManager de Flask en el archivo principal.

Generar formularios con Flask-WTF para el inicio de sesión.

Asegurar que el frontend utilice las clases CSS del archivo reciclado para mantener la consistencia visual.