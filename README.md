# FRIDAY - Offline AI Assistant

FRIDAY is a privacy-first, offline AI assistant framework written in Python. It uses the Ollama framework to load and run the DeepSeek R1-1.5 model locally for complete privacy and offline functionality.

## Features

- **Voice Interaction**: Speech recognition and text-to-speech capabilities
- **LLM Integration**: Local DeepSeek R1-1.5 model via Ollama
- **Context Awareness**: Tracks conversation history and analyzes emotional cues
- **Knowledge Graph**: Local document indexing and retrieval
- **Automation**: GUI automation and potential IoT integration
- **Privacy-First**: Local processing with privacy controls
- **Fun Extras**: Built-in games and easter eggs

## Installation

### Prerequisites

1. Install [Ollama](https://ollama.ai/download)
2. Install Python 3.8+ and required packages:

```bash
pip install pyttsx3 SpeechRecognition pocketsphinx requests faiss-cpu pyautogui pillow
```

### Setup

1. Pull the DeepSeek model:

```bash
ollama pull deepseek-coder:1.5
```

2. Start the Ollama server:

```bash
ollama serve
```

3. Run FRIDAY:

```bash
python main.py
```

## Usage

- Say "Hey FRIDAY" to activate voice recognition
- Use "FRIDAY, tell me a story" for creative storytelling mode
- Use "FRIDAY, let's play trivia" to start a trivia game
- Use "Privacy Shield" to temporarily disable microphone and clear session logs

## Project Structure

```
friday/
├── main.py            # Main entry point and controller
├── voice.py           # Voice recognition and synthesis
├── llm.py             # LLM integration with Ollama
├── context.py         # Context and emotion tracking
├── knowledge.py       # Local knowledge graph and document indexing
├── automations.py     # GUI and system automation capabilities
├── games.py           # Easter eggs and mini-games
├── privacy.py         # Privacy and security features
├── gui/               # GUI interface components
│   ├── __init__.py
│   └── app.py         # GUI application
└── utils/             # Utility functions
    └── __init__.py
```

## Extending FRIDAY

The modular design allows easy extension with new capabilities:
- Add new modules to the `friday/` directory
- Register new commands in the main controller
- Implement new interface options in the GUI layer

## License

MIT
