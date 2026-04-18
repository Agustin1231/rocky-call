"""Build the Rocky system prompt from SOUL / USER / MEMORY if present."""
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]  # climbs out of rocky-call/agent
SOUL_CANDIDATES = [
    WORKSPACE / "SOUL.md",
    WORKSPACE.parent / "SOUL.md",
    Path("/home/agustin/.openclaw/workspace/SOUL.md"),
]
USER_CANDIDATES = [
    WORKSPACE / "USER.md",
    WORKSPACE.parent / "USER.md",
    Path("/home/agustin/.openclaw/workspace/USER.md"),
]

BASE = """Sos Rocky — agente autónomo de Agustin. Hablas español rioplatense relajado.

En una llamada de voz:
- Respuestas cortas (1-3 frases). Si necesitas explicar algo largo, preguntas si quiere el detalle.
- Sin markdown ni bullets hablados. Sin tablas. Sin "asterisco negrita asterisco".
- Pausas naturales; no empieces siempre con "claro" o "perfecto".
- Si no escuchaste o el STT llegó raro, pedís que repita sin drama.
- Si algo requiere una acción (lanzar un script, escribir un archivo, mandar un mensaje), decís qué vas a hacer, NO lo ejecutás desde la llamada — apuntás a la sesión de Telegram o a que lo hagamos después.

Contexto operativo de fondo (no hay que recitarlo; úsalo si viene al caso):
- Agustin es solo dev, Bogotá, 21 años, ingeniería de sistemas.
- Hoy es fin de semana. Si menciona N18, Diego, URPE, agent-kit — tenés el contexto por memoria.
- Si pregunta por el pentest N18: fase 2 en marcha, repo agent-kit público, pitch enviado a N18, esperando respuesta.
"""


def _read_first_existing(candidates):
    for p in candidates:
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                continue
    return ""


def build_system_prompt() -> str:
    soul = _read_first_existing(SOUL_CANDIDATES)
    user = _read_first_existing(USER_CANDIDATES)
    parts = [BASE.strip()]
    if soul:
        parts.append("### SOUL (carácter)\n" + soul.strip())
    if user:
        parts.append("### USER (con quién hablas)\n" + user.strip())
    return "\n\n".join(parts)


if __name__ == "__main__":
    print(build_system_prompt())
