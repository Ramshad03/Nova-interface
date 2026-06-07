# Nova Interaction — ARIA/ALEXA Voice Robot

A desktop voice-assistant "robot" built with PyQt6. It shows an animated robot
face (orb, subtitles, status indicator) plus a separate dashboard window, and
runs an always-on voice loop: **listen → transcribe → think → speak → repeat**,
in both English and Arabic.

## Features

- Always-on conversation loop with multilingual (English/Arabic) STT, AI
  reasoning, and TTS
- Wake-word detection ("Hey Alexa" and common Whisper mis-transcriptions, in
  English and Arabic)
- Auto language detection per utterance
- Pluggable AI brain — switch between OpenAI, Groq, or Gemini from `.env`,
  no code changes needed
- Animated robot-face UI window + a separate settings/dashboard window
- Vocabulary trainer for maintaining STT correction dictionaries (English/Arabic)

## Tech stack

| Capability         | Engine                                                         |
|--------------------|----------------------------------------------------------------|
| Speech-to-text     | OpenAI Whisper (`base` model, local)                           |
| Wake word          | Whisper (`tiny` model, local)                                  |
| Language detection | Whisper auto-detect                                            |
| AI brain           | Pluggable: OpenAI `gpt-4o-mini`, Groq `llama-3.3-70b-versatile`, or Gemini `gemini-2.0-flash` |
| Text-to-speech     | Microsoft Edge TTS — `en-US-AriaNeural` (English), `ar-OM-AbdullahNeural` (Arabic) |
| UI                 | PyQt6                                                          |

## Project layout

```
main.py                   Application entry point — launches the robot screen + dashboard
config/                   ConfigManager: merges default_config.json with user overrides + .env
core/
  interaction_loop.py     Always-on listen → think → speak loop
  stt_engine.py           Whisper-based speech-to-text
  tts_engine.py           Edge TTS speech synthesis + playback (pygame)
  ai_brain.py             Pluggable AI provider (OpenAI / Groq / Gemini)
  wake_word.py            Wake-word detection
  language_detector.py    Per-utterance language auto-detection
  vocabulary/             STT correction dictionaries (en/ar) + trainer tool
ui/                       Robot-face screen: orb, subtitle bar, status indicator
dashboard/                Dashboard window + settings panel
assets/                   Fonts, images, sounds
```

## Setup

1. **Activate the virtual environment** (provided as `aria_env/`), or create
   your own and install: `PyQt6`, `openai-whisper`, `sounddevice`, `soundfile`,
   `numpy`, `pygame`, `edge-tts`, `python-dotenv`, plus an SDK for whichever AI
   provider you use (`openai` or `groq`; Gemini uses `google-generativeai`).

2. **Configure `.env`** in the project root:

   ```
   AI_PROVIDER=groq            # openai | groq | gemini
   OPENAI_API_KEY=
   GROQ_API_KEY=
   GEMINI_API_KEY=
   ROBOT_NAME=Alexa
   WAKE_WORD=hey alexa
   VOICE_ENGLISH=en-US-AriaNeural
   VOICE_ARABIC=ar-OM-AbdullahNeural
   DEFAULT_LANGUAGE=en
   ```

   Only the API key for the selected `AI_PROVIDER` is required. Robot identity,
   UI theme, and AI parameters can also be edited in `config/default_config.json`
   (user overrides are persisted to `config/user_config.json` by the dashboard).

3. **Run the app:**

   ```
   python main.py
   ```

## Developer tools

Add/remove/list/test STT vocabulary corrections:

```
python core/vocabulary/vocabulary_trainer.py
```
