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

## Running the tests

Run the full suite from the project root:

```
python -m unittest discover -s tests -v
```

Run a single module:

```
python -m unittest tests.test_board
python -m unittest tests.test_verifier
python -m unittest tests.test_solver
python -m unittest tests.test_generator
```

### Test coverage

| Module              | What is tested                                                                 |
|---------------------|--------------------------------------------------------------------------------|
| `tests/test_board.py`     | Cell defaults, `set`/`get`, given-cell protection, boundary errors, row/col/box queries, candidates, `copy`, `from_grid`, `to_grid` |
| `tests/test_verifier.py`  | **Success:** empty board valid, partial puzzle valid, fully solved board valid and complete. **Failure:** row/col/box duplicates flagged, conflict cells identified by position, multiple independent conflicts all reported, complete-but-invalid board not marked solved. `is_valid_placement` success and failure cases. |
| `tests/test_solver.py`    | Known puzzle solves to expected answer, `solve_copy` leaves original unchanged, unsolvable board returns `None`, solution count (unique, multiple, zero) |
| `tests/test_generator.py` | Given-cell counts per difficulty, harder difficulties have fewer givens, no conflicts in output, puzzle is not pre-solved, solution is valid and unique |

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
