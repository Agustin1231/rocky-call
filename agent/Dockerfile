FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent.py rocky_persona.py ./

# Pre-download silero VAD weights so cold-start is faster
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

CMD ["python", "agent.py", "start"]
