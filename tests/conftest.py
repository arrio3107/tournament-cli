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
def two_players():
    """Create a list of 2 player names."""
    return ["Alice", "Bob"]


@pytest.fixture
def three_players():
    """Create a list of 3 player names."""
    return ["Alice", "Bob", "Charlie"]


@pytest.fixture
def six_players():
    """Create a list of 6 player names."""
    return ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]


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
def sample_match_1v1():
    """Create a 1v1 match."""
    return Match(
        id=1,
        team1=("Alice",),
        team2=("Bob",)
    )


@pytest.fixture
def sample_match_3v3():
    """Create a 3v3 match."""
    return Match(
        id=1,
        team1=("Alice", "Bob", "Charlie"),
        team2=("Dave", "Eve", "Frank")
    )


@pytest.fixture
def sample_match_1v2():
    """Create a 1v2 asymmetric match."""
    return Match(
        id=1,
        team1=("Alice",),
        team2=("Bob", "Charlie")
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
    """Create a sample 2v2 tournament with 4 players."""
    players = [Player(name=name) for name in four_players]
    matches = generate_matches(four_players, team1_size=2, team2_size=2, shuffle=False)
    return Tournament(
        name="Test Tournament",
        players=players,
        matches=matches,
        team1_size=2,
        team2_size=2,
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def sample_tournament_1v1(four_players):
    """Create a sample 1v1 tournament with 4 players."""
    players = [Player(name=name) for name in four_players]
    matches = generate_matches(four_players, team1_size=1, team2_size=1, shuffle=False)
    return Tournament(
        name="Test 1v1 Tournament",
        players=players,
        matches=matches,
        team1_size=1,
        team2_size=1,
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def sample_tournament_1v2(three_players):
    """Create a sample 1v2 tournament with 3 players."""
    players = [Player(name=name) for name in three_players]
    matches = generate_matches(three_players, team1_size=1, team2_size=2, shuffle=False)
    return Tournament(
        name="Test 1v2 Tournament",
        players=players,
        matches=matches,
        team1_size=1,
        team2_size=2,
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
