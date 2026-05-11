#!/usr/bin/env python3
import sys
import os
import argparse

# This reconfigure MUST happen before any other imports — the generator and display
# modules print things at import time on some paths, and if stdout is still in
# cp1252 mode (Windows default) those prints will blow up on box-drawing characters.
# line_buffering=True means every print() flushes immediately so we don't need to
# sprinkle flush=True everywhere, which matters most in pipe environments like Git Bash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

from generator import Difficulty
from game import Game

_WINPTY_WARNING = """
  ╔══════════════════════════════════════════════════════════════╗
  ║  Git Bash / mintty detected without winpty                  ║
  ║                                                              ║
  ║  In this mode Ctrl+C cannot stop the process and arrow      ║
  ║  keys require pressing Enter after each key press.          ║
  ║                                                              ║
  ║  For full support (arrow keys, Ctrl+C, instant keypresses)  ║
  ║  run the game with:                                          ║
  ║                                                              ║
  ║    winpty python main.py                                     ║
  ║                                                              ║
  ║  winpty ships with Git for Windows — no install needed.     ║
  ╚══════════════════════════════════════════════════════════════╝
"""


def _wait_for_enter() -> None:
    # Python's input() goes through the text-layer which doesn't reliably flush in
    # mintty pipe environments — os.read() bypasses all of that and reads the raw
    # bytes directly from the file descriptor, same approach as _read_line() in player.py
    sys.stdout.write("  Press Enter to continue in degraded mode... ")
    sys.stdout.flush()
    try:
        os.read(sys.stdin.fileno(), 256)
    except (EOFError, OSError):
        pass  # if stdin is completely broken just continue anyway


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sudoku",
        description="Terminal Sudoku — generate, play, and auto-solve puzzles.",
    )
    parser.add_argument(
        "-d", "--difficulty",
        choices=[d.value for d in Difficulty],
        default=Difficulty.MEDIUM.value,
        help="Starting difficulty (default: medium)",
    )
    return parser.parse_args()
    # TODO: add a --name flag so the scoreboard can greet the player by name
    #       and eventually separate stats per player on a shared machine


def main() -> None:
    args = parse_args()
    game = Game()
    game._difficulty = Difficulty(args.difficulty)

    # Warn the player upfront if we detected a degraded input environment.
    # Better to set expectations before the game starts than to have them discover
    # the limitations by pressing Ctrl+C and nothing happening mid-game.
    if game._player._reader.line_mode:
        print(_WINPTY_WARNING)
        _wait_for_enter()

    # TODO: load the scoreboard from disk here and pass it into Game so it can
    #       update and display wins/best times. Something like:
    #         scoreboard = Scoreboard.load("~/.sudoku_scores.json")
    #         game = Game(scoreboard=scoreboard)
    #       and then save it back on game.run() return

    try:
        game.run()
    except KeyboardInterrupt:
        # Can only get here via winpty or a real console — Git Bash without winpty
        # can't deliver SIGINT to a Windows process, so this is mostly for POSIX / CMD
        print("\n  Bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
