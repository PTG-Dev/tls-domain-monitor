

import os
import sys
import time
from pathlib import Path

# Enable ANSI escape codes on Windows (no-op on other platforms)
if sys.platform == "win32":
    os.system("")

_AUDIO_FILE = Path(__file__).parent / "more" / "booting.mp3"


def _play_audio() -> None:
    """Plays booting.mp3 in the background (non-blocking). Silent if unavailable."""
    try:
        _platform: str = sys.platform
        if _platform == "win32":
            import ctypes
            winmm = ctypes.windll.winmm
            path  = str(_AUDIO_FILE).replace("/", "\\")
            winmm.mciSendStringW(f'open "{path}" type mpegvideo alias bgm', None, 0, None)
            winmm.mciSendStringW('play bgm', None, 0, None)
        else:
            import subprocess
            _PLAYERS = [
                ["ffplay",  "-nodisp", "-autoexit", "-loglevel", "quiet"],
                ["mpg123",  "-q"],
                ["mpg321",  "-q"],
                ["mplayer", "-really-quiet"],
            ]
            for cmd in _PLAYERS:
                try:
                    subprocess.Popen(
                        cmd + [str(_AUDIO_FILE)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    break
                except FileNotFoundError:
                    continue
    except Exception:
        pass

_PALE_BLUE = "\033[96m"
_PALE_MAUVE = "\033[38;5;183m"
_RESET     = "\033[0m"

_BANNER_LINES = [
    r"       ::::::::   ::::::::      :::     ::::    ::: ",
    r"     :+:    :+: :+:    :+:   :+: :+:   :+:+:   :+:",
    r"    +:+        +:+         +:+   +:+  :+:+:+  +:+",
    r"   +#++:++#++ +#+        +#++:++#++: +#+ +:+ +#+",
    r"         +#+ +#+        +#+     +#+ +#+  +#+#+#",
    r" #+#    #+# #+#    #+# #+#     #+# #+#   #+#+#",
    r" ########   ########  ###     ### ###    ####",
    r"",
    r"         :::   :::   :::::::::: v1.1",
    r"       :+:+: :+:+:  :+:",
    r"     +:+ +:+:+ +:+ +:+",
    r"    +#+  +:+  +#+ +#++:++#",
    r"   +#+       +#+ +#+",
    r"  #+#       #+# #+#",
    r" ###       ### ##########",
    r"",
    r"  Certificate Transparency Log Monitor By PTGDev",
    r"  Powered by Google CT Log — ct.googleapis.com",
]

# Delay between frames (seconds). Lower = faster animation.
_FRAME_DELAY = 0.055
_STEP        = 2      # columns revealed per frame


def show_boot_screen() -> None:
    """
    Clears the terminal, plays booting.mp3, reveals the ASCII banner
    left-to-right in pale blue, waits 2 seconds, then switches the
    terminal color to dark pink for all subsequent output.
    """
    # Clear the terminal
    os.system("cls" if sys.platform == "win32" else "clear")

    _play_audio()

    max_width = max(len(line) for line in _BANNER_LINES)
    n_lines   = len(_BANNER_LINES)
    padded    = [line.ljust(max_width) for line in _BANNER_LINES]

    # Build column checkpoints: 0, 2, 4, ..., max_width
    cols = list(range(0, max_width, _STEP)) + [max_width]

    sys.stdout.write("\n")

    for frame, col in enumerate(cols):
        # From the second frame onward, move cursor back up to redraw
        if frame > 0:
            sys.stdout.write(f"\033[{n_lines}A")

        for line in padded:
            sys.stdout.write(f"\r{_PALE_BLUE}{line[:col]}{_RESET}\n")

        sys.stdout.flush()
        time.sleep(_FRAME_DELAY)

    sys.stdout.write("\n")
    sys.stdout.flush()

    # Pause 2 seconds before the menu appears
    time.sleep(2)

    # Switch terminal color to pale mauve for everything that follows
    sys.stdout.write(_PALE_MAUVE)
    sys.stdout.flush()
