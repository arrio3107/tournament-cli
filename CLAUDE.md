# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_models.py

# Run a single test
pytest tests/test_models.py::TestPlayerStats::test_points_calculation

# Run with verbose output
pytest -v --tb=short

# Run the CLI
tournament-cli --help

# Build standalone binary
pip install pyinstaller
pyinstaller tournament-cli.spec
```

## Architecture

This is a 2v2 tournament management CLI built with Typer and Rich. It generates all valid matchups where every player plays with and against every other player.

### Module Structure

- **models.py** - Data classes: `PlayerStats`, `Player`, `Match`, `Tournament`. All include `to_dict()`/`from_dict()` for JSON serialization.
- **matchmaking.py** - `generate_matches()` creates all valid 2v2 matchups using combinatorics. Formula: `n(n-1)(n-2)(n-3)/8` matches for n players.
- **storage.py** - JSON persistence to `tournaments/` directory. Maintains current tournament state via `_current_tournament` global and `.config.json`.
- **display.py** - Rich console output. `calculate_partnership_stats()` and `calculate_team_stats()` compute derived statistics.
- **export.py** - Markdown and PDF export. Uses weasyprint for PDF generation.
- **cli.py** - Typer commands. Uses `require_tournament()` decorator pattern for commands needing a loaded tournament.

### Data Flow

1. `new` command → `generate_matches()` → `Tournament` created → saved to JSON
2. `play` command → updates `Match.score1/score2` → updates `Player.stats` → saves
3. `standings`/`teams` → reads from current tournament, displays computed rankings

### Testing

Tests use `temp_tournaments_dir` fixture to isolate storage. CLI tests use Typer's `CliRunner`. The `sample_tournament` fixture creates a 4-player tournament with 3 matches.

### Python Version Compatibility

Must use `Optional[X]` instead of `X | None` for Python 3.9 support.
