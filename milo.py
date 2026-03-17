#!/usr/bin/env python3
"""MILO Terminal — MUTHR/Alien: Isolation style AI chat interface."""

import curses
import time
import textwrap
import sys
import requests

from config import GATEWAY_URL, GATEWAY_TOKEN, AGENT_ID

ASCII_ART = [
    " __  __ ___ _     ___  ",
    "|  \\/  |_ _| |   / _ \\ ",
    "| |\\/| || || |  | | | |",
    "| |  | || || |__| |_| |",
    "|_|  |_|___|_____\\___/ ",
]

BOOT_LOG = [
    "MILO TERMINAL v1.0",
    "MUTHR SYSTEMS — WEYLAND-YUTANI CORP",
    "------------------------------------",
    "Initializing core subsystems...",
    "Loading neural interface drivers...",
    "Establishing uplink to gateway...",
    "Authenticating agent credentials...",
    "Agent ID: main — AUTHORIZED",
    "Communication channel OPEN",
    "------------------------------------",
    "MILO ONLINE. READY FOR INPUT.",
]

# Color pair IDs
AMBER = 1
GREEN = 2
DIM_AMBER = 3
WHITE = 4
SEPARATOR = 5


def send_message(messages):
    """Send messages to OpenClaw API and return assistant reply."""
    headers = {
        "Authorization": f"Bearer {GATEWAY_TOKEN}",
        "x-openclaw-agent-id": AGENT_ID,
        "Content-Type": "application/json",
    }
    payload = {
        "model": "main",
        "messages": messages,
        "stream": False,
    }
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "[ERROR] Cannot connect to gateway. Is OpenClaw running?"
    except requests.exceptions.Timeout:
        return "[ERROR] Request timed out."
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] HTTP {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def boot_sequence(stdscr):
    """Display the boot sequence with typewriter effect."""
    curses.curs_set(0)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Print ASCII art centered
    art_start_row = max(0, h // 2 - len(ASCII_ART) - len(BOOT_LOG) // 2 - 2)
    art_start_col = max(0, (w - len(ASCII_ART[0])) // 2)

    for i, line in enumerate(ASCII_ART):
        row = art_start_row + i
        if row < h:
            stdscr.addstr(row, art_start_col, line, curses.color_pair(AMBER) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.04)

    # Blank line
    log_start_row = art_start_row + len(ASCII_ART) + 1

    for i, line in enumerate(BOOT_LOG):
        row = log_start_row + i
        if row >= h:
            break
        col = max(0, (w - len(line)) // 2)
        # Typewriter effect per character for first line, fast for rest
        if i == 0:
            for j, ch in enumerate(line):
                if col + j < w:
                    stdscr.addch(row, col + j, ch, curses.color_pair(AMBER))
                    stdscr.refresh()
                    time.sleep(0.04)
        else:
            attr = curses.color_pair(DIM_AMBER)
            if "ONLINE" in line or "AUTHORIZED" in line or "OPEN" in line:
                attr = curses.color_pair(GREEN) | curses.A_BOLD
            elif line.startswith("---"):
                attr = curses.color_pair(DIM_AMBER)
            stdscr.addstr(row, col, line, attr)
            stdscr.refresh()
            time.sleep(0.05)

    time.sleep(0.8)


def wrap_text(text, width):
    """Wrap text to width, returning list of lines."""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
        else:
            wrapped = textwrap.wrap(paragraph, width - 2) if paragraph.strip() else [""]
            lines.extend(wrapped)
    return lines


def main(stdscr):
    # Setup colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(AMBER, 214, -1)       # amber on default bg
    curses.init_pair(GREEN, 82, -1)        # bright green
    curses.init_pair(DIM_AMBER, 172, -1)   # dim amber
    curses.init_pair(WHITE, 255, -1)       # near white
    curses.init_pair(SEPARATOR, 240, -1)   # dark gray

    # Black background
    stdscr.bkgd(' ', curses.color_pair(DIM_AMBER))
    stdscr.clear()

    boot_sequence(stdscr)

    curses.curs_set(1)
    stdscr.clear()
    stdscr.refresh()

    messages = []
    chat_lines = []  # list of (text, color_pair, bold)
    input_buf = []
    scroll_offset = 0

    def get_dims():
        h, w = stdscr.getmaxyx()
        chat_h = max(3, int(h * 0.80) - 1)
        input_row = chat_h + 1
        return h, w, chat_h, input_row

    def render():
        nonlocal scroll_offset
        h, w, chat_h, input_row = get_dims()
        stdscr.erase()

        # Draw chat area
        visible = chat_lines[-(chat_h + scroll_offset):] if scroll_offset == 0 else \
                  chat_lines[-(chat_h + scroll_offset):len(chat_lines) - scroll_offset]
        visible = visible[-chat_h:]

        for i, (text, cpair, bold) in enumerate(visible):
            if i >= chat_h:
                break
            attr = curses.color_pair(cpair)
            if bold:
                attr |= curses.A_BOLD
            try:
                stdscr.addnstr(i, 0, text.ljust(w)[:w], w, attr)
            except curses.error:
                pass

        # Separator
        sep_row = chat_h
        try:
            sep = ("─" * (w - 1))
            stdscr.addstr(sep_row, 0, sep, curses.color_pair(SEPARATOR))
        except curses.error:
            pass

        # Input line
        prefix = "» "
        input_text = "".join(input_buf)
        display = (prefix + input_text)[-w + 1:]
        try:
            stdscr.addstr(input_row, 0, display, curses.color_pair(AMBER) | curses.A_BOLD)
        except curses.error:
            pass

        # Position cursor
        cursor_x = min(len(prefix) + len(input_text), w - 1)
        try:
            stdscr.move(input_row, cursor_x)
        except curses.error:
            pass

        stdscr.refresh()

    def add_chat_line(text, cpair, bold=False, prefix=""):
        h, w, chat_h, input_row = get_dims()
        full = prefix + text if prefix else text
        wrapped = wrap_text(full, w)
        for line in wrapped:
            chat_lines.append((line, cpair, bold))

    def add_divider():
        h, w, chat_h, input_row = get_dims()
        chat_lines.append(("─" * (w - 1), SEPARATOR, False))

    # Welcome message
    add_chat_line("MILO TERMINAL READY", AMBER, bold=True)
    add_chat_line("Type your message and press ENTER. Ctrl+C to exit.", DIM_AMBER)
    add_divider()

    render()

    # Key handling
    stdscr.keypad(True)

    while True:
        try:
            key = stdscr.get_wch()
        except KeyboardInterrupt:
            break

        if key == "\x03":  # Ctrl+C
            break
        elif key in (curses.KEY_ENTER, "\n", "\r"):
            user_text = "".join(input_buf).strip()
            input_buf.clear()
            if not user_text:
                render()
                continue

            # Display user message
            add_divider()
            add_chat_line(f"YOU  {user_text}", AMBER, bold=True, prefix="")
            # Actually display with label
            # Re-do: pop the last entry and redo with proper label
            chat_lines.pop()
            h, w, chat_h, input_row = get_dims()
            label = "YOU  "
            wrapped = wrap_text(label + user_text, w)
            for i, line in enumerate(wrapped):
                chat_lines.append((line, AMBER, i == 0))

            scroll_offset = 0
            render()

            # Show "thinking" indicator
            h, w, chat_h, input_row = get_dims()
            try:
                thinking_msg = "MILO  ..."
                stdscr.addnstr(chat_h - 1, 0, thinking_msg, w, curses.color_pair(GREEN) | curses.A_DIM)
                stdscr.refresh()
            except curses.error:
                pass

            # Send to API
            messages.append({"role": "user", "content": user_text})
            reply = send_message(messages)
            messages.append({"role": "assistant", "content": reply})

            # Display reply
            h, w, chat_h, input_row = get_dims()
            label = "MILO  "
            wrapped = wrap_text(label + reply, w)
            for i, line in enumerate(wrapped):
                chat_lines.append((line, GREEN, i == 0))

            scroll_offset = 0
            render()

        elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            if input_buf:
                input_buf.pop()
            render()
        elif key == curses.KEY_UP:
            scroll_offset = min(scroll_offset + 1, max(0, len(chat_lines) - 3))
            render()
        elif key == curses.KEY_DOWN:
            scroll_offset = max(0, scroll_offset - 1)
            render()
        elif key == curses.KEY_RESIZE:
            render()
        elif isinstance(key, str) and key.isprintable():
            input_buf.append(key)
            render()
        elif isinstance(key, int) and 32 <= key < 127:
            input_buf.append(chr(key))
            render()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nMILO Terminal — session ended.")
        sys.exit(0)
