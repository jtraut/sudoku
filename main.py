#!/usr/bin/env python3
import sys
import argparse

# Windows terminals default to cp1252; force UTF-8 for box-drawing characters.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from generator import Difficulty
from game import Game


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
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n  Bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
