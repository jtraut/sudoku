#!/usr/bin/env python3
import sys
import argparse

# Force UTF-8 and line-buffering so every print() flushes immediately in pipe
# environments (Git Bash / mintty) without needing explicit flush=True calls.
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


def main() -> None:
    args = parse_args()
    game = Game()
    game._difficulty = Difficulty(args.difficulty)
    if game._player._reader.line_mode:
        print(_WINPTY_WARNING)
        input("  Press Enter to continue in degraded mode...")
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n  Bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
