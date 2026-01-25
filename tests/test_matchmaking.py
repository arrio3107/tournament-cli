"""Tests for tournament_cli.matchmaking module."""

import pytest
from collections import Counter

from tournament_cli.matchmaking import generate_matches, calculate_expected_matches


class TestGenerateMatches:
    """Tests for generate_matches function."""

    def test_minimum_players(self, four_players):
        """Test with minimum 4 players."""
        matches = generate_matches(four_players, shuffle=False)
        assert len(matches) == 3

    def test_five_players(self, five_players):
        """Test with 5 players."""
        matches = generate_matches(five_players, shuffle=False)
        assert len(matches) == 15

    def test_six_players(self):
        """Test with 6 players."""
        players = ["A", "B", "C", "D", "E", "F"]
        matches = generate_matches(players, shuffle=False)
        assert len(matches) == 45

    def test_too_few_players(self):
        """Test that fewer than 4 players raises ValueError."""
        with pytest.raises(ValueError, match="Need at least 4 players"):
            generate_matches(["A", "B", "C"])

    def test_three_players_raises(self):
        """Test that exactly 3 players raises ValueError."""
        with pytest.raises(ValueError):
            generate_matches(["A", "B", "C"])

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            generate_matches([])

    def test_no_duplicate_matches(self, five_players):
        """Test that no match is generated twice."""
        matches = generate_matches(five_players, shuffle=False)

        # Create normalized match keys
        match_keys = set()
        for match in matches:
            t1 = tuple(sorted(match.team1))
            t2 = tuple(sorted(match.team2))
            key = tuple(sorted([t1, t2]))
            assert key not in match_keys, f"Duplicate match found: {key}"
            match_keys.add(key)

    def test_no_player_overlap_in_match(self, five_players):
        """Test that no match has overlapping players in teams."""
        matches = generate_matches(five_players, shuffle=False)
        for match in matches:
            team1_set = set(match.team1)
            team2_set = set(match.team2)
            assert len(team1_set & team2_set) == 0, "Player overlap found"

    def test_all_players_play_together(self, four_players):
        """Test that every pair of players play together as teammates."""
        matches = generate_matches(four_players, shuffle=False)

        # Count teammate pairings
        teammate_pairs = Counter()
        for match in matches:
            teammate_pairs[tuple(sorted(match.team1))] += 1
            teammate_pairs[tuple(sorted(match.team2))] += 1

        # With 4 players, each pair should play together at least once
        from itertools import combinations
        for pair in combinations(four_players, 2):
            assert tuple(sorted(pair)) in teammate_pairs

    def test_all_players_play_against_each_other(self, four_players):
        """Test that every pair of players play against each other."""
        matches = generate_matches(four_players, shuffle=False)

        # Count opponent pairings
        opponent_pairs = Counter()
        for match in matches:
            for p1 in match.team1:
                for p2 in match.team2:
                    opponent_pairs[tuple(sorted([p1, p2]))] += 1

        # Each pair should face each other
        from itertools import combinations
        for pair in combinations(four_players, 2):
            assert tuple(sorted(pair)) in opponent_pairs

    def test_match_ids_sequential(self, five_players):
        """Test that match IDs are sequential starting from 1."""
        matches = generate_matches(five_players, shuffle=False)
        ids = [m.id for m in matches]
        assert ids == list(range(1, len(matches) + 1))

    def test_shuffle_changes_order(self, five_players):
        """Test that shuffle=True produces different order (probabilistic)."""
        # Generate multiple times and check if at least one is different
        base_matches = generate_matches(five_players, shuffle=False)
        base_order = [(m.team1, m.team2) for m in base_matches]

        different_found = False
        for _ in range(10):
            shuffled = generate_matches(five_players, shuffle=True)
            shuffled_order = [(m.team1, m.team2) for m in shuffled]
            if shuffled_order != base_order:
                different_found = True
                break

        assert different_found, "Shuffle should produce different order"

    def test_shuffle_same_matches(self, five_players):
        """Test that shuffle produces same matches, just different order."""
        unshuffled = generate_matches(five_players, shuffle=False)
        shuffled = generate_matches(five_players, shuffle=True)

        # Create sets of normalized match keys
        def match_key(m):
            t1 = tuple(sorted(m.team1))
            t2 = tuple(sorted(m.team2))
            return tuple(sorted([t1, t2]))

        unshuffled_keys = {match_key(m) for m in unshuffled}
        shuffled_keys = {match_key(m) for m in shuffled}

        assert unshuffled_keys == shuffled_keys

    def test_matches_are_unplayed(self, four_players):
        """Test that generated matches are unplayed."""
        matches = generate_matches(four_players)
        for match in matches:
            assert match.played is False
            assert match.score1 is None
            assert match.score2 is None


class TestCalculateExpectedMatches:
    """Tests for calculate_expected_matches function."""

    def test_four_players(self):
        """Test expected matches for 4 players."""
        assert calculate_expected_matches(4) == 3

    def test_five_players(self):
        """Test expected matches for 5 players."""
        assert calculate_expected_matches(5) == 15

    def test_six_players(self):
        """Test expected matches for 6 players."""
        assert calculate_expected_matches(6) == 45

    def test_seven_players(self):
        """Test expected matches for 7 players."""
        assert calculate_expected_matches(7) == 105

    def test_eight_players(self):
        """Test expected matches for 8 players."""
        assert calculate_expected_matches(8) == 210

    def test_fewer_than_four(self):
        """Test that fewer than 4 players returns 0."""
        assert calculate_expected_matches(3) == 0
        assert calculate_expected_matches(2) == 0
        assert calculate_expected_matches(1) == 0
        assert calculate_expected_matches(0) == 0

    def test_matches_generated_vs_expected(self, five_players):
        """Test that generated matches match expected count."""
        expected = calculate_expected_matches(len(five_players))
        matches = generate_matches(five_players)
        assert len(matches) == expected

    def test_formula_consistency(self):
        """Test the formula n(n-1)(n-2)(n-3)/8 for various n."""
        for n in range(4, 10):
            expected = (n * (n - 1) * (n - 2) * (n - 3)) // 8
            assert calculate_expected_matches(n) == expected
