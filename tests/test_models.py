"""Tests for tournament_cli.models module."""

import pytest
from datetime import datetime

from tournament_cli.models import PlayerStats, Player, Match, Tournament


class TestPlayerStats:
    """Tests for PlayerStats dataclass."""

    def test_default_values(self):
        """Test that default values are all zero."""
        stats = PlayerStats()
        assert stats.wins == 0
        assert stats.draws == 0
        assert stats.losses == 0
        assert stats.goals_scored == 0
        assert stats.goals_conceded == 0

    def test_games_played(self, sample_player_stats):
        """Test games_played property calculation."""
        assert sample_player_stats.games_played == 10  # 5 + 2 + 3

    def test_points_calculation(self, sample_player_stats):
        """Test points calculation (3 for win, 1 for draw)."""
        assert sample_player_stats.points == 17  # 5*3 + 2*1

    def test_goal_difference(self, sample_player_stats):
        """Test goal difference calculation."""
        assert sample_player_stats.goal_difference == 5  # 15 - 10

    def test_win_rate(self, sample_player_stats):
        """Test win rate percentage."""
        assert sample_player_stats.win_rate == 50.0  # 5/10 * 100

    def test_win_rate_zero_games(self):
        """Test win rate when no games played."""
        stats = PlayerStats()
        assert stats.win_rate == 0.0

    def test_to_dict(self, sample_player_stats):
        """Test serialization to dictionary."""
        data = sample_player_stats.to_dict()
        assert data == {
            "wins": 5,
            "draws": 2,
            "losses": 3,
            "goals_scored": 15,
            "goals_conceded": 10,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "wins": 3,
            "draws": 1,
            "losses": 2,
            "goals_scored": 8,
            "goals_conceded": 6,
        }
        stats = PlayerStats.from_dict(data)
        assert stats.wins == 3
        assert stats.draws == 1
        assert stats.losses == 2
        assert stats.goals_scored == 8
        assert stats.goals_conceded == 6

    def test_from_dict_with_missing_keys(self):
        """Test deserialization with missing keys uses defaults."""
        stats = PlayerStats.from_dict({})
        assert stats.wins == 0
        assert stats.goals_scored == 0

    def test_roundtrip_serialization(self, sample_player_stats):
        """Test that to_dict and from_dict are inverses."""
        data = sample_player_stats.to_dict()
        restored = PlayerStats.from_dict(data)
        assert restored == sample_player_stats


class TestPlayer:
    """Tests for Player dataclass."""

    def test_default_stats(self):
        """Test that player has default empty stats."""
        player = Player(name="Test")
        assert player.name == "Test"
        assert player.stats.games_played == 0

    def test_with_stats(self, sample_player):
        """Test player with provided stats."""
        assert sample_player.name == "Alice"
        assert sample_player.stats.wins == 3

    def test_to_dict(self, sample_player):
        """Test serialization to dictionary."""
        data = sample_player.to_dict()
        assert data["name"] == "Alice"
        assert "stats" in data
        assert data["stats"]["wins"] == 3

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "Bob",
            "stats": {"wins": 2, "draws": 0, "losses": 1, "goals_scored": 5, "goals_conceded": 3}
        }
        player = Player.from_dict(data)
        assert player.name == "Bob"
        assert player.stats.wins == 2

    def test_roundtrip_serialization(self, sample_player):
        """Test that to_dict and from_dict are inverses."""
        data = sample_player.to_dict()
        restored = Player.from_dict(data)
        assert restored.name == sample_player.name
        assert restored.stats == sample_player.stats


class TestMatch:
    """Tests for Match dataclass."""

    def test_unplayed_match(self, sample_match_unplayed):
        """Test properties of unplayed match."""
        assert sample_match_unplayed.played is False
        assert sample_match_unplayed.winner is None
        assert sample_match_unplayed.loser is None
        assert sample_match_unplayed.is_draw is False

    def test_played_match_winner(self, sample_match_played):
        """Test winner detection."""
        assert sample_match_played.played is True
        assert sample_match_played.winner == ("Alice", "Bob")
        assert sample_match_played.loser == ("Charlie", "Dave")
        assert sample_match_played.is_draw is False

    def test_played_match_team2_wins(self):
        """Test when team2 wins."""
        match = Match(id=1, team1=("A", "B"), team2=("C", "D"), score1=1, score2=3)
        assert match.winner == ("C", "D")
        assert match.loser == ("A", "B")

    def test_draw_match(self, sample_match_draw):
        """Test draw detection."""
        assert sample_match_draw.played is True
        assert sample_match_draw.is_draw is True
        assert sample_match_draw.winner is None
        assert sample_match_draw.loser is None

    def test_to_dict(self, sample_match_played):
        """Test serialization to dictionary."""
        data = sample_match_played.to_dict()
        assert data["id"] == 1
        assert data["team1"] == ["Alice", "Bob"]
        assert data["team2"] == ["Charlie", "Dave"]
        assert data["score1"] == 3
        assert data["score2"] == 1

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": 5,
            "team1": ["A", "B"],
            "team2": ["C", "D"],
            "score1": 2,
            "score2": 0
        }
        match = Match.from_dict(data)
        assert match.id == 5
        assert match.team1 == ("A", "B")
        assert match.team2 == ("C", "D")
        assert match.score1 == 2
        assert match.score2 == 0

    def test_from_dict_unplayed(self):
        """Test deserializing unplayed match."""
        data = {"id": 1, "team1": ["A", "B"], "team2": ["C", "D"]}
        match = Match.from_dict(data)
        assert match.score1 is None
        assert match.score2 is None
        assert match.played is False


class TestTournament:
    """Tests for Tournament dataclass."""

    def test_tournament_creation(self, sample_tournament):
        """Test basic tournament creation."""
        assert sample_tournament.name == "Test Tournament"
        assert len(sample_tournament.players) == 4
        assert len(sample_tournament.matches) == 3  # 4 players = 3 matches

    def test_total_matches(self, sample_tournament):
        """Test total_matches property."""
        assert sample_tournament.total_matches == 3

    def test_played_matches_initial(self, sample_tournament):
        """Test played_matches when no matches played."""
        assert sample_tournament.played_matches == 0

    def test_remaining_matches(self, sample_tournament):
        """Test remaining_matches property."""
        assert sample_tournament.remaining_matches == 3

    def test_completion_percentage_zero(self, sample_tournament):
        """Test completion percentage at start."""
        assert sample_tournament.completion_percentage == 0.0

    def test_completion_percentage_partial(self, sample_tournament):
        """Test completion percentage after some matches."""
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 1
        assert sample_tournament.completion_percentage == pytest.approx(33.33, rel=0.1)

    def test_completion_percentage_empty_tournament(self):
        """Test completion percentage with no matches."""
        tournament = Tournament(name="Empty", players=[], matches=[])
        assert tournament.completion_percentage == 0.0

    def test_get_player_found(self, sample_tournament):
        """Test finding a player by name."""
        player = sample_tournament.get_player("Alice")
        assert player is not None
        assert player.name == "Alice"

    def test_get_player_case_insensitive(self, sample_tournament):
        """Test finding player is case insensitive."""
        player = sample_tournament.get_player("ALICE")
        assert player is not None
        assert player.name == "Alice"

    def test_get_player_not_found(self, sample_tournament):
        """Test get_player returns None for unknown player."""
        assert sample_tournament.get_player("Unknown") is None

    def test_get_next_match(self, sample_tournament):
        """Test getting next unplayed match."""
        next_match = sample_tournament.get_next_match()
        assert next_match is not None
        assert next_match.played is False

    def test_get_next_match_all_played(self, sample_tournament):
        """Test get_next_match when all matches played."""
        for match in sample_tournament.matches:
            match.score1 = 1
            match.score2 = 0
        assert sample_tournament.get_next_match() is None

    def test_get_match_by_id(self, sample_tournament):
        """Test getting match by ID."""
        match = sample_tournament.get_match_by_id(1)
        assert match is not None
        assert match.id == 1

    def test_get_match_by_id_not_found(self, sample_tournament):
        """Test get_match_by_id returns None for invalid ID."""
        assert sample_tournament.get_match_by_id(999) is None

    def test_to_dict(self, sample_tournament):
        """Test serialization to dictionary."""
        data = sample_tournament.to_dict()
        assert data["name"] == "Test Tournament"
        assert len(data["players"]) == 4
        assert len(data["matches"]) == 3
        assert "created_at" in data

    def test_from_dict(self, sample_tournament):
        """Test deserialization from dictionary."""
        data = sample_tournament.to_dict()
        restored = Tournament.from_dict(data)
        assert restored.name == sample_tournament.name
        assert len(restored.players) == len(sample_tournament.players)
        assert len(restored.matches) == len(sample_tournament.matches)

    def test_roundtrip_serialization(self, sample_tournament):
        """Test complete serialization roundtrip."""
        data = sample_tournament.to_dict()
        restored = Tournament.from_dict(data)
        assert restored.name == sample_tournament.name
        assert restored.created_at == sample_tournament.created_at
        assert [p.name for p in restored.players] == [p.name for p in sample_tournament.players]
