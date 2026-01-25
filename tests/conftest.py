"""Pytest fixtures for tournament-cli tests."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from tournament_cli.models import Tournament, Player, PlayerStats, Match
from tournament_cli.matchmaking import generate_matches


@pytest.fixture
def sample_player_stats():
    """Create sample player statistics."""
    return PlayerStats(
        wins=5,
        draws=2,
        losses=3,
        goals_scored=15,
        goals_conceded=10
    )


@pytest.fixture
def sample_player():
    """Create a sample player."""
    return Player(
        name="Alice",
        stats=PlayerStats(wins=3, draws=1, losses=1, goals_scored=10, goals_conceded=5)
    )


@pytest.fixture
def sample_match_unplayed():
    """Create an unplayed match."""
    return Match(
        id=1,
        team1=("Alice", "Bob"),
        team2=("Charlie", "Dave")
    )


@pytest.fixture
def sample_match_played():
    """Create a played match with team1 winning."""
    return Match(
        id=1,
        team1=("Alice", "Bob"),
        team2=("Charlie", "Dave"),
        score1=3,
        score2=1
    )


@pytest.fixture
def sample_match_draw():
    """Create a played match that ended in a draw."""
    return Match(
        id=2,
        team1=("Alice", "Bob"),
        team2=("Charlie", "Dave"),
        score1=2,
        score2=2
    )


@pytest.fixture
def four_players():
    """Create a list of 4 player names."""
    return ["Alice", "Bob", "Charlie", "Dave"]


@pytest.fixture
def five_players():
    """Create a list of 5 player names."""
    return ["Alice", "Bob", "Charlie", "Dave", "Eve"]


@pytest.fixture
def sample_tournament(four_players):
    """Create a sample tournament with 4 players."""
    players = [Player(name=name) for name in four_players]
    matches = generate_matches(four_players, shuffle=False)
    return Tournament(
        name="Test Tournament",
        players=players,
        matches=matches,
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def temp_tournaments_dir(monkeypatch):
    """Create a temporary directory for tournament storage."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Patch the storage module to use temp directory
    import tournament_cli.storage as storage
    monkeypatch.setattr(storage, 'TOURNAMENTS_DIR', temp_path)
    monkeypatch.setattr(storage, 'CONFIG_FILE', temp_path / ".config.json")
    monkeypatch.setattr(storage, '_current_tournament', None)

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
