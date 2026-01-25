"""Tests for tournament_cli.display module."""

import pytest
from io import StringIO

from tournament_cli.models import Tournament, Player, PlayerStats, Match
from tournament_cli.display import (
    calculate_partnership_stats,
    calculate_team_stats,
)


class TestCalculatePartnershipStats:
    """Tests for calculate_partnership_stats function."""

    def test_no_played_matches(self, sample_tournament):
        """Test partnership stats when no matches played."""
        stats = calculate_partnership_stats("Alice", sample_tournament)
        assert stats == {}

    def test_with_played_matches(self, sample_tournament):
        """Test partnership stats with played matches."""
        # Play first match: Alice & Bob vs Charlie & Dave (3-1)
        sample_tournament.matches[0].score1 = 3
        sample_tournament.matches[0].score2 = 1

        stats = calculate_partnership_stats("Alice", sample_tournament)

        # Alice played with Bob
        assert "Bob" in stats
        assert stats["Bob"]["wins"] == 1
        assert stats["Bob"]["draws"] == 0
        assert stats["Bob"]["losses"] == 0

    def test_partnership_loss(self, sample_tournament):
        """Test partnership stats with a loss."""
        # Assume Alice & Bob are team1 in match 0
        # Make them lose
        sample_tournament.matches[0].score1 = 0
        sample_tournament.matches[0].score2 = 2

        stats = calculate_partnership_stats("Alice", sample_tournament)

        if "Bob" in stats:  # If Alice and Bob are teammates in this match
            assert stats["Bob"]["losses"] == 1
        # Otherwise Charlie or Dave should be the partner

    def test_partnership_draw(self, sample_tournament):
        """Test partnership stats with a draw."""
        sample_tournament.matches[0].score1 = 1
        sample_tournament.matches[0].score2 = 1

        stats = calculate_partnership_stats("Alice", sample_tournament)

        # Find Alice's partner in this match
        match = sample_tournament.matches[0]
        if "Alice" in match.team1:
            partner = match.team1[0] if match.team1[1] == "Alice" else match.team1[1]
        else:
            partner = match.team2[0] if match.team2[1] == "Alice" else match.team2[1]

        assert partner in stats
        assert stats[partner]["draws"] == 1

    def test_unknown_player(self, sample_tournament):
        """Test partnership stats for unknown player."""
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 1

        stats = calculate_partnership_stats("Unknown", sample_tournament)
        assert stats == {}


class TestCalculateTeamStats:
    """Tests for calculate_team_stats function."""

    def test_no_played_matches(self, sample_tournament):
        """Test team stats when no matches played."""
        stats = calculate_team_stats(sample_tournament)
        assert stats == []

    def test_with_played_matches(self, sample_tournament):
        """Test team stats with played matches."""
        # Play a match
        sample_tournament.matches[0].score1 = 3
        sample_tournament.matches[0].score2 = 1

        stats = calculate_team_stats(sample_tournament)

        assert len(stats) == 2  # Two teams played
        # Winning team should have higher points
        assert stats[0]["points"] >= stats[1]["points"]

    def test_team_stats_fields(self, sample_tournament):
        """Test that team stats contain all required fields."""
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 0

        stats = calculate_team_stats(sample_tournament)

        for team_stat in stats:
            assert "players" in team_stat
            assert "wins" in team_stat
            assert "draws" in team_stat
            assert "losses" in team_stat
            assert "goals_for" in team_stat
            assert "goals_against" in team_stat
            assert "games" in team_stat
            assert "points" in team_stat
            assert "goal_diff" in team_stat
            assert "win_rate" in team_stat

    def test_team_stats_sorted_by_points(self, sample_tournament):
        """Test that team stats are sorted by points (descending)."""
        # Play multiple matches
        for i, match in enumerate(sample_tournament.matches):
            match.score1 = i + 1
            match.score2 = 0

        stats = calculate_team_stats(sample_tournament)

        # Verify sorted by points
        points = [s["points"] for s in stats]
        assert points == sorted(points, reverse=True)

    def test_team_stats_goals(self, sample_tournament):
        """Test that goals are correctly attributed."""
        match = sample_tournament.matches[0]
        match.score1 = 5
        match.score2 = 2

        stats = calculate_team_stats(sample_tournament)

        # Find team1's stats
        team1_key = tuple(sorted(match.team1))
        team1_stats = None
        for s in stats:
            if tuple(sorted(s["players"])) == team1_key:
                team1_stats = s
                break

        assert team1_stats is not None
        assert team1_stats["goals_for"] == 5
        assert team1_stats["goals_against"] == 2
        assert team1_stats["goal_diff"] == 3

    def test_team_stats_win_rate(self, sample_tournament):
        """Test win rate calculation."""
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 0

        stats = calculate_team_stats(sample_tournament)

        # Winner should have 100% win rate
        winning_team = stats[0]
        assert winning_team["win_rate"] == 100.0

        # Loser should have 0% win rate
        losing_team = stats[1]
        assert losing_team["win_rate"] == 0.0

    def test_team_stats_draw(self, sample_tournament):
        """Test team stats with a draw."""
        sample_tournament.matches[0].score1 = 1
        sample_tournament.matches[0].score2 = 1

        stats = calculate_team_stats(sample_tournament)

        # Both teams should have 1 point
        for team_stat in stats:
            assert team_stat["draws"] == 1
            assert team_stat["points"] == 1


class TestTeamStatsSorting:
    """Tests for team stats sorting order."""

    def test_sort_by_points_then_goal_diff(self):
        """Test sorting by points, then goal difference."""
        # Create tournament where teams have same points but different GD
        players = [Player(name=n) for n in ["A", "B", "C", "D"]]
        matches = [
            Match(id=1, team1=("A", "B"), team2=("C", "D"), score1=1, score2=0),
            Match(id=2, team1=("A", "C"), team2=("B", "D"), score1=3, score2=0),
        ]
        tournament = Tournament(name="Test", players=players, matches=matches)

        stats = calculate_team_stats(tournament)

        # Team with better goal difference should be ranked higher
        # when points are equal
        if len(stats) > 1 and stats[0]["points"] == stats[1]["points"]:
            assert stats[0]["goal_diff"] >= stats[1]["goal_diff"]
