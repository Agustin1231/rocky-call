# rocky-call

Llamada de voz en tiempo real con Rocky.

**Pipeline:** browser WebRTC ↔ LiveKit Cloud ↔ agente Python que corre
Deepgram (STT, `nova-2-general` en `es-419`) → Claude Opus 4.7 → ElevenLabs
(Voice ID `HJAIwgFDzw3Kk9aW7RYr`, speed 1.1).

## Servicios

| Servicio | Qué hace | Puerto |
|----------|----------|--------|
| `agent`  | Worker de LiveKit Agents que joinea las rooms y corre el pipeline de voz. | — |
| `backend` | FastAPI: emite tokens JWT de LiveKit y sirve el build estático del web. | 8000 |
| `web` | React + Vite, UI minimal "Call Rocky". En prod se compila dentro del contenedor del backend. | — |

## Run local

```bash
cp .env.example .env
# completar las 4 keys: LiveKit x3, Deepgram, Anthropic ya está, ElevenLabs

# backend + agente en docker-compose
docker compose up --build

# web en dev (otra terminal) — hot reload con proxy a :8000
cd web && npm install && npm run dev
# abrir http://localhost:5173
```

## Deploy en Coolify

- Un servicio por cada Dockerfile (`agent/`, `backend/`).
- Para el backend, exponer 8000 detrás de `rocky.agustinynatalia.site`.
- Secretos desde las env vars del proyecto.
- Auto-deploy vía webhook GitHub → main.

## Latencia esperada

~800 ms de fin-de-frase a primer audio de respuesta (Deepgram endpointing
~200 ms + Claude time-to-first-token + ElevenLabs stream start). Interrupciones
mid-speech soportadas por LiveKit Agents.

## Costo

Aprox USD 0.35–0.50 / minuto de llamada (Deepgram + Claude Opus + ElevenLabs).
Free tier de LiveKit Cloud: 5 000 min/mes.
