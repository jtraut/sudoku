# Sudoku
Python implementation of terminal-based Sudoku; leveraging Claude Code.

## Running the game

```
python main.py              # medium difficulty
python main.py -d easy      # easy | medium | hard | expert
```

## Controls

| Key(s)                         | Action                              |
|--------------------------------|-------------------------------------|
| Arrow keys / `W` `A` `S` `D` | Move cursor                        |
| `1` – `9`                      | Place a digit                       |
| `0` / `Space` / `X` / `Delete` | Clear a cell                        |
| `Tab`                          | Auto-solve (asks for confirmation)  |
| `N`                            | New game (same difficulty)          |
| `F`                            | Cycle difficulty and start new game |
| `C`                            | Check board for conflicts           |
| `?`                            | Toggle help overlay                 |
| `Q` / `Ctrl+C`                 | Quit                                |

## Project structure

| File            | Responsibility                                      |
|-----------------|-----------------------------------------------------|
| `main.py`       | Entry point and CLI argument parsing                |
| `game.py`       | Game loop orchestrator                              |
| `board.py`      | `Board` / `Cell` classes and grid state             |
| `generator.py`  | Randomised puzzle generation with uniqueness check  |
| `solver.py`     | Backtracking solver with MRV heuristic              |
| `verifier.py`   | Conflict detection and completion checking          |
| `display.py`    | ANSI terminal rendering with colour and cursor      |
| `player.py`     | Platform-aware keypress reader and action parser    |
