# MILO Terminal

A MUTHR-style (Alien: Isolation) ncurses terminal interface for chatting with MILO — your AI operator.

## Features

- Amber-on-black retro CRT aesthetic
- MILO boot splash sequence
- Split-panel chat UI (history + input)
- Streams responses from OpenClaw gateway (OpenAI-compatible API)
- Pairs beautifully with [Cool Retro Term](https://github.com/Swordfish90/cool-retro-term)

## Requirements

- Python 3.8+
- `requests`, `curses` (stdlib)
- OpenClaw gateway running locally

## Usage

```bash
python3 milo.py
```

## Configuration

Set your gateway token in `config.py` or via environment variable:

```bash
export MILO_GATEWAY_TOKEN="your_token_here"
export MILO_GATEWAY_URL="http://127.0.0.1:18789"
```

## Credits

Inspired by [alien-console](https://github.com/brenns10/alien-console) by brenns10.

---

*MILO — Mechanical Intelligent Learning Operator*
