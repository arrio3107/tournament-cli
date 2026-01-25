"""Tests for tournament_cli.storage module."""

import pytest
import json
from pathlib import Path

from tournament_cli.models import Tournament, Player, Match
from tournament_cli import storage


class TestStorageFunctions:
    """Tests for storage functions."""

    def test_ensure_tournaments_dir(self, temp_tournaments_dir):
        """Test that tournaments directory is created."""
        # Directory should be created by fixture
        assert temp_tournaments_dir.exists()

    def test_get_tournament_path(self, temp_tournaments_dir):
        """Test tournament path generation."""
        path = storage.get_tournament_path("Test Cup")
        assert path.name == "Test_Cup.json"

    def test_get_tournament_path_special_chars(self, temp_tournaments_dir):
        """Test tournament path with special characters."""
        path = storage.get_tournament_path("Test/Cup:2024")
        assert "/" not in path.name
        assert ":" not in path.name

    def test_save_and_load_tournament(self, temp_tournaments_dir, sample_tournament):
        """Test saving and loading a tournament."""
        storage.save_tournament(sample_tournament)

        loaded = storage.load_tournament("Test Tournament")
        assert loaded is not None
        assert loaded.name == sample_tournament.name
        assert len(loaded.players) == len(sample_tournament.players)

    def test_load_nonexistent_tournament(self, temp_tournaments_dir):
        """Test loading a tournament that doesn't exist."""
        result = storage.load_tournament("Nonexistent")
        assert result is None

    def test_list_tournaments_empty(self, temp_tournaments_dir):
        """Test listing tournaments when none exist."""
        tournaments = storage.list_tournaments()
        assert tournaments == []

    def test_list_tournaments(self, temp_tournaments_dir, sample_tournament):
        """Test listing tournaments."""
        storage.save_tournament(sample_tournament)

        tournaments = storage.list_tournaments()
        assert "Test Tournament" in tournaments

    def test_list_tournaments_multiple(self, temp_tournaments_dir):
        """Test listing multiple tournaments."""
        t1 = Tournament(name="Alpha", players=[], matches=[])
        t2 = Tournament(name="Beta", players=[], matches=[])
        t3 = Tournament(name="Gamma", players=[], matches=[])

        storage.save_tournament(t1)
        storage.save_tournament(t2)
        storage.save_tournament(t3)

        tournaments = storage.list_tournaments()
        assert tournaments == ["Alpha", "Beta", "Gamma"]  # Should be sorted

    def test_delete_tournament(self, temp_tournaments_dir, sample_tournament):
        """Test deleting a tournament."""
        storage.save_tournament(sample_tournament)
        assert storage.load_tournament("Test Tournament") is not None

        result = storage.delete_tournament("Test Tournament")
        assert result is True
        assert storage.load_tournament("Test Tournament") is None

    def test_delete_nonexistent_tournament(self, temp_tournaments_dir):
        """Test deleting a tournament that doesn't exist."""
        result = storage.delete_tournament("Nonexistent")
        assert result is False


class TestConfigFunctions:
    """Tests for config-related functions."""

    def test_get_config_empty(self, temp_tournaments_dir):
        """Test getting config when none exists."""
        config = storage.get_config()
        assert config == {}

    def test_save_and_get_config(self, temp_tournaments_dir):
        """Test saving and getting config."""
        storage.save_config({"key": "value"})
        config = storage.get_config()
        assert config == {"key": "value"}

    def test_get_current_tournament_name_none(self, temp_tournaments_dir):
        """Test getting current tournament name when none set."""
        name = storage.get_current_tournament_name()
        assert name is None

    def test_set_and_get_current_tournament_name(self, temp_tournaments_dir):
        """Test setting and getting current tournament name."""
        storage.set_current_tournament_name("My Tournament")
        name = storage.get_current_tournament_name()
        assert name == "My Tournament"

    def test_clear_current_tournament_name(self, temp_tournaments_dir):
        """Test clearing current tournament name."""
        storage.set_current_tournament_name("My Tournament")
        storage.set_current_tournament_name(None)
        name = storage.get_current_tournament_name()
        assert name is None


class TestCurrentTournamentState:
    """Tests for current tournament state management."""

    def test_get_current_tournament_none(self, temp_tournaments_dir):
        """Test getting current tournament when none loaded."""
        # Reset global state
        storage._current_tournament = None
        tournament = storage.get_current_tournament()
        assert tournament is None

    def test_set_and_get_current_tournament(self, temp_tournaments_dir, sample_tournament):
        """Test setting and getting current tournament."""
        storage.set_current_tournament(sample_tournament)
        current = storage.get_current_tournament()
        assert current is not None
        assert current.name == sample_tournament.name

    def test_current_tournament_persists_name(self, temp_tournaments_dir, sample_tournament):
        """Test that setting current tournament persists the name."""
        storage.set_current_tournament(sample_tournament)
        name = storage.get_current_tournament_name()
        assert name == sample_tournament.name

    def test_clear_current_tournament(self, temp_tournaments_dir, sample_tournament):
        """Test clearing current tournament."""
        storage.set_current_tournament(sample_tournament)
        storage.set_current_tournament(None)
        assert storage.get_current_tournament() is None
        assert storage.get_current_tournament_name() is None

    def test_save_current_tournament(self, temp_tournaments_dir, sample_tournament):
        """Test saving current tournament."""
        storage.set_current_tournament(sample_tournament)
        path = storage.save_current_tournament()
        assert path is not None
        assert path.exists()

    def test_save_current_tournament_none(self, temp_tournaments_dir):
        """Test saving when no current tournament."""
        storage._current_tournament = None
        path = storage.save_current_tournament()
        assert path is None

    def test_load_from_config_on_get(self, temp_tournaments_dir, sample_tournament):
        """Test that get_current_tournament loads from config if needed."""
        # Save tournament and set as current
        storage.save_tournament(sample_tournament)
        storage.set_current_tournament_name(sample_tournament.name)

        # Clear in-memory cache
        storage._current_tournament = None

        # Should load from config
        current = storage.get_current_tournament()
        assert current is not None
        assert current.name == sample_tournament.name


class TestTournamentDataIntegrity:
    """Tests for data integrity during save/load cycles."""

    def test_match_scores_preserved(self, temp_tournaments_dir, sample_tournament):
        """Test that match scores are preserved."""
        sample_tournament.matches[0].score1 = 3
        sample_tournament.matches[0].score2 = 1

        storage.save_tournament(sample_tournament)
        loaded = storage.load_tournament("Test Tournament")

        assert loaded.matches[0].score1 == 3
        assert loaded.matches[0].score2 == 1

    def test_player_stats_preserved(self, temp_tournaments_dir, sample_tournament):
        """Test that player stats are preserved."""
        sample_tournament.players[0].stats.wins = 5
        sample_tournament.players[0].stats.goals_scored = 10

        storage.save_tournament(sample_tournament)
        loaded = storage.load_tournament("Test Tournament")

        assert loaded.players[0].stats.wins == 5
        assert loaded.players[0].stats.goals_scored == 10

    def test_tournament_timestamp_preserved(self, temp_tournaments_dir, sample_tournament):
        """Test that tournament timestamp is preserved."""
        storage.save_tournament(sample_tournament)
        loaded = storage.load_tournament("Test Tournament")

        assert loaded.created_at == sample_tournament.created_at
