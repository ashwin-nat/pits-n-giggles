# Local CPU voice engineer

Voice runs independently of the telemetry launcher as a user service, with access
to the logged-in user's PipeWire audio session:

**Microphone → faster-whisper → local Ollama + live MCP telemetry → Piper → speakers.**

The existing models remain in `models/whisper/` and `models/piper/`. The current
configuration uses Whisper `small.en`, Ollama `llama3.1:8b`, and Piper
`en_GB-alan-medium`. No GPU or Gemini credential is required.

## Use

Start the telemetry application first. The installed workstation services are:

- Application: `systemctl status pits-ngiggles.service`
- Voice: `systemctl --user status pits-ngiggles-voice.service`

Say **“radio, what is my tyre wear?”** or **“engineer, how much fuel do I have?”**.
A bare **“radio”** opens an eight-second follow-up window after “Go ahead.”
Voice starts automatically with the user's service manager at login; audio
hardware must be available. It does not require a browser microphone permission.

```bash
systemctl --user stop pits-ngiggles-voice.service
systemctl --user start pits-ngiggles-voice.service
journalctl --user -u pits-ngiggles-voice.service -n 50 --no-pager
```

Stopping the voice service leaves telemetry running. Do not also launch the app
with `--voice` while this service is active: that would create a second listener.

## Local-only behavior

`png_voice.json` selects models, microphone preference, wake words, and proactive
callouts. Keep `backend` set to `local`. The standalone service rejects cloud
backends and non-loopback Ollama/MCP endpoints. Missing Whisper models fail
explicitly; local STT never falls back to Google. Local TTS uses Piper or its
existing offline fallback, never Edge TTS. The service disables Hugging Face
network access and uses cached models.

Microphone selection rejects output monitors. It preserves a valid default input
if the configured headset is absent, or selects an available non-Bluetooth input
when the default is an output monitor. The selected source is bound directly
to the voice process, even when WirePlumber retains a monitor as the global
default. It does not switch unrelated Bluetooth headsets. Choose the intended physical input and suitable gain in system audio
settings. The service does not save audio recordings; recognized speech and
engineer replies can appear in its local journal.

## Check without opening the microphone

```bash
HF_HUB_OFFLINE=1 poetry run python -m apps.voice --check
```

This checks the configured Ollama model and MCP tool discovery, loads the CPU
Whisper model, and synthesizes Piper audio without recording or playback. It is
not proof that a physical microphone or speaker works.

## Installation on this workstation

The template `deploy/pits-ngiggles-voice.service` uses the project-local `.venv`
and `/home/keith/pits-n-giggles`; adjust paths for other users or installations.
Install it into `~/.config/systemd/user/`, reload the user manager, and enable it.
The obsolete system-level Node service remains disabled. No extra HTTP port is
opened by this replacement; it consumes the launcher's existing MCP endpoint.

## Validation

- Unit regressions cover local-only failure policy, microphone selection,
  supervision of both workers, and graceful shutdown.
- Live smoke checks cover the cached models, local Ollama answers, and MCP.
- Physical microphone capture and audible responses require an interactive check.
