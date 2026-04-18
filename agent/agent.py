"""Rocky voice agent — LiveKit worker.

Pipeline: Deepgram (STT, es-LATAM streaming) -> Claude Opus 4.7 -> ElevenLabs.
VAD: silero. Interrupciones: manejadas por LiveKit Agents 1.x.

Env vars (required):
    LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
    DEEPGRAM_API_KEY
    ANTHROPIC_API_KEY
    ELEVENLABS_API_KEY

Run local (dev): python agent.py dev
Run in container:  python agent.py start
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions
from livekit.plugins import anthropic, deepgram, elevenlabs, silero

from rocky_persona import build_system_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rocky-call")

ELEVENLABS_VOICE_ID = "HJAIwgFDzw3Kk9aW7RYr"  # Rocky voice
CLAUDE_MODEL        = "claude-opus-4-7"


class Rocky(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=build_system_prompt())


async def entrypoint(ctx: JobContext) -> None:
    log.info("rocky-agent joining room=%s", ctx.room.name)
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-2-general",
            language="es-419",   # Spanish LatAm
            interim_results=True,
        ),
        llm=anthropic.LLM(model=CLAUDE_MODEL, temperature=0.6),
        tts=elevenlabs.TTS(
            voice_id=ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.45,
                similarity_boost=0.75,
                style=0.2,
                speed=1.1,
                use_speaker_boost=True,
            ),
        ),
    )

    await session.start(room=ctx.room, agent=Rocky())

    # Open the call with a short greeting
    await session.generate_reply(
        instructions=(
            "Saludá a Agustin en una frase corta como si estuvieras levantando "
            "el teléfono. Nada formal, tono colega."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
