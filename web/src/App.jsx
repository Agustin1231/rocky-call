import { useCallback, useEffect, useRef, useState } from 'react'
import { Room, RoomEvent, Track } from 'livekit-client'

const STATES = {
  idle:       { label: 'Tocá para llamar',      dot: '#4a5680' },
  connecting: { label: 'Conectando…',           dot: '#ffb347' },
  listening:  { label: 'Escuchando',            dot: '#5ec9ff' },
  thinking:   { label: 'Pensando…',             dot: '#c084fc' },
  speaking:   { label: 'Hablando',              dot: '#00e5a8' },
  error:      { label: 'Error — intentá otra vez', dot: '#ff6b6b' },
}

export default function App() {
  const [state, setState]   = useState('idle')
  const [error, setError]   = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const roomRef   = useRef(null)
  const audioRef  = useRef(null)
  const startedAt = useRef(null)
  const tickRef   = useRef(null)

  const isActive = state !== 'idle' && state !== 'error'

  // elapsed timer
  useEffect(() => {
    if (!isActive) {
      if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null }
      return
    }
    if (!startedAt.current) startedAt.current = Date.now()
    tickRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt.current) / 1000))
    }, 500)
    return () => clearInterval(tickRef.current)
  }, [isActive])

  const hangup = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect()
      roomRef.current = null
    }
    startedAt.current = null
    setElapsed(0)
    setState('idle')
  }, [])

  const call = useCallback(async () => {
    setError(null)
    setState('connecting')
    try {
      const resp = await fetch('/api/token', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ name: 'Agustin' }),
      })
      if (!resp.ok) throw new Error(`token ${resp.status}`)
      const { token, url } = await resp.json()

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      room.on(RoomEvent.TrackSubscribed, (track, pub, participant) => {
        if (track.kind !== Track.Kind.Audio) return
        const el = track.attach()
        el.autoplay = true
        audioRef.current?.appendChild(el)
        setState('listening')
      })

      // LiveKit Agents sends active_speakers / agent state via metadata.
      // Cheap heuristic: when the agent publishes audio energy, we mark speaking.
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const agent = speakers.find(p => p.identity?.startsWith('agent') || p.isAgent)
        if (agent) setState('speaking')
        else if (isActive) setState('listening')
      })

      room.on(RoomEvent.Disconnected, () => {
        roomRef.current = null
        setState('idle')
      })

      await room.connect(url, token)
      await room.localParticipant.setMicrophoneEnabled(true)
      roomRef.current = room
      setState('listening')
    } catch (e) {
      console.error(e)
      setError(String(e.message || e))
      setState('error')
    }
  }, [isActive])

  const s = STATES[state] || STATES.idle
  const mmss = `${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`

  return (
    <div className="page">
      <header className="hdr">
        <div className="brand">rocky · call</div>
        <div className="net">{isActive ? mmss : 'en línea'}</div>
      </header>

      <main className="main">
        <div className={`orb ${state}`}>
          <div className="orb-core" />
          <div className="orb-ring" />
        </div>

        <div className="label">
          <span className="dot" style={{ background: s.dot }} />
          <span>{s.label}</span>
        </div>

        {error && <div className="err">{error}</div>}

        <div className="ctrls">
          {!isActive ? (
            <button className="btn call" onClick={call}>
              Llamar a Rocky
            </button>
          ) : (
            <button className="btn hangup" onClick={hangup}>
              Colgar
            </button>
          )}
        </div>

        <p className="hint">
          Rocky usa Claude Opus 4.7 con Deepgram + ElevenLabs. Latencia ~1 s,
          podés interrumpirlo hablando encima.
        </p>
      </main>

      <div ref={audioRef} style={{ display: 'none' }} />
    </div>
  )
}
