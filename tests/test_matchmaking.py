"""Tests for tournament_cli.matchmaking module."""

import pytest
from collections import Counter

from tournament_cli.matchmaking import (
    generate_matches,
    calculate_expected_matches,
    get_minimum_players,
    get_sitting_out,
    optimize_match_order,
)


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


class TestGetMinimumPlayers:
    """Tests for get_minimum_players function."""

    def test_1v1_minimum(self):
        """Test minimum players for 1v1."""
        assert get_minimum_players(1, 1) == 2

    def test_2v2_minimum(self):
        """Test minimum players for 2v2."""
        assert get_minimum_players(2, 2) == 4

    def test_3v3_minimum(self):
        """Test minimum players for 3v3."""
        assert get_minimum_players(3, 3) == 6

    def test_1v2_minimum(self):
        """Test minimum players for 1v2."""
        assert get_minimum_players(1, 2) == 3

    def test_2v3_minimum(self):
        """Test minimum players for 2v3."""
        assert get_minimum_players(2, 3) == 5


class TestGenerate1v1Matches:
    """Tests for 1v1 match generation."""

    def test_minimum_players(self, two_players):
        """Test with minimum 2 players."""
        matches = generate_matches(two_players, team1_size=1, team2_size=1, shuffle=False)
        assert len(matches) == 1

    def test_four_players_1v1(self, four_players):
        """Test 1v1 with 4 players."""
        matches = generate_matches(four_players, team1_size=1, team2_size=1, shuffle=False)
        # C(4, 2) = 6 matches
        assert len(matches) == 6

    def test_five_players_1v1(self, five_players):
        """Test 1v1 with 5 players."""
        matches = generate_matches(five_players, team1_size=1, team2_size=1, shuffle=False)
        # C(5, 2) = 10 matches
        assert len(matches) == 10

    def test_1v1_match_structure(self, four_players):
        """Test that 1v1 matches have single-player teams."""
        matches = generate_matches(four_players, team1_size=1, team2_size=1, shuffle=False)
        for match in matches:
            assert len(match.team1) == 1
            assert len(match.team2) == 1

    def test_1v1_no_duplicate_matches(self, four_players):
        """Test that no match is generated twice in 1v1."""
        matches = generate_matches(four_players, team1_size=1, team2_size=1, shuffle=False)
        match_keys = set()
        for match in matches:
            key = tuple(sorted([match.team1[0], match.team2[0]]))
            assert key not in match_keys
            match_keys.add(key)

    def test_1v1_too_few_players(self):
        """Test that fewer than 2 players raises ValueError."""
        with pytest.raises(ValueError, match="Need at least 2 players"):
            generate_matches(["A"], team1_size=1, team2_size=1)

    def test_1v1_expected_matches(self):
        """Test expected matches formula for 1v1."""
        for n in range(2, 8):
            expected = calculate_expected_matches(n, team1_size=1, team2_size=1)
            assert expected == (n * (n - 1)) // 2


class TestGenerate3v3Matches:
    """Tests for 3v3 match generation."""

    def test_minimum_players(self, six_players):
        """Test with minimum 6 players."""
        matches = generate_matches(six_players, team1_size=3, team2_size=3, shuffle=False)
        # C(6, 3) * C(3, 3) / 2 = 20 * 1 / 2 = 10 matches
        assert len(matches) == 10

    def test_3v3_match_structure(self, six_players):
        """Test that 3v3 matches have three-player teams."""
        matches = generate_matches(six_players, team1_size=3, team2_size=3, shuffle=False)
        for match in matches:
            assert len(match.team1) == 3
            assert len(match.team2) == 3

    def test_3v3_no_player_overlap(self, six_players):
        """Test that no match has overlapping players in teams."""
        matches = generate_matches(six_players, team1_size=3, team2_size=3, shuffle=False)
        for match in matches:
            assert len(set(match.team1) & set(match.team2)) == 0

    def test_3v3_too_few_players(self):
        """Test that fewer than 6 players raises ValueError."""
        with pytest.raises(ValueError, match="Need at least 6 players"):
            generate_matches(["A", "B", "C", "D", "E"], team1_size=3, team2_size=3)


class TestGenerateAsymmetricMatches:
    """Tests for asymmetric match generation (e.g., 1v2, 2v3)."""

    def test_1v2_minimum_players(self, three_players):
        """Test 1v2 with minimum 3 players."""
        matches = generate_matches(three_players, team1_size=1, team2_size=2, shuffle=False)
        # Each solo player (3) vs each pair that doesn't include them: 3 * 1 = 3 matches
        assert len(matches) == 3

    def test_1v2_four_players(self, four_players):
        """Test 1v2 with 4 players."""
        matches = generate_matches(four_players, team1_size=1, team2_size=2, shuffle=False)
        # C(4, 1) * C(3, 2) = 4 * 3 = 12 matches
        assert len(matches) == 12

    def test_1v2_match_structure(self, four_players):
        """Test that 1v2 matches have correct team sizes."""
        matches = generate_matches(four_players, team1_size=1, team2_size=2, shuffle=False)
        for match in matches:
            assert len(match.team1) == 1
            assert len(match.team2) == 2

    def test_2v3_minimum_players(self, five_players):
        """Test 2v3 with minimum 5 players."""
        matches = generate_matches(five_players, team1_size=2, team2_size=3, shuffle=False)
        # C(5, 2) * C(3, 3) = 10 * 1 = 10 matches
        assert len(matches) == 10

    def test_2v3_match_structure(self, five_players):
        """Test that 2v3 matches have correct team sizes."""
        matches = generate_matches(five_players, team1_size=2, team2_size=3, shuffle=False)
        for match in matches:
            assert len(match.team1) == 2
            assert len(match.team2) == 3

    def test_asymmetric_no_player_overlap(self, four_players):
        """Test that asymmetric matches have no overlapping players."""
        matches = generate_matches(four_players, team1_size=1, team2_size=2, shuffle=False)
        for match in matches:
            assert len(set(match.team1) & set(match.team2)) == 0

    def test_1v2_too_few_players(self):
        """Test that fewer than 3 players raises ValueError for 1v2."""
        with pytest.raises(ValueError, match="Need at least 3 players"):
            generate_matches(["A", "B"], team1_size=1, team2_size=2)

    def test_2v1_same_as_1v2(self, four_players):
        """Test that 2v1 generates same number of matches as 1v2 (order matters)."""
        matches_1v2 = generate_matches(four_players, team1_size=1, team2_size=2, shuffle=False)
        matches_2v1 = generate_matches(four_players, team1_size=2, team2_size=1, shuffle=False)
        assert len(matches_1v2) == len(matches_2v1)

    def test_2v1_match_structure(self, four_players):
        """Test that 2v1 matches have team1 with 2 players."""
        matches = generate_matches(four_players, team1_size=2, team2_size=1, shuffle=False)
        for match in matches:
            assert len(match.team1) == 2
            assert len(match.team2) == 1


class TestCalculateExpectedMatchesVariableSizes:
    """Tests for calculate_expected_matches with variable team sizes."""

    def test_1v1_expected_matches(self):
        """Test expected matches for 1v1 mode."""
        # C(n, 2) = n(n-1)/2
        assert calculate_expected_matches(2, team1_size=1, team2_size=1) == 1
        assert calculate_expected_matches(3, team1_size=1, team2_size=1) == 3
        assert calculate_expected_matches(4, team1_size=1, team2_size=1) == 6
        assert calculate_expected_matches(5, team1_size=1, team2_size=1) == 10

    def test_3v3_expected_matches(self):
        """Test expected matches for 3v3 mode."""
        # C(n, 3) * C(n-3, 3) / 2
        assert calculate_expected_matches(6, team1_size=3, team2_size=3) == 10

    def test_1v2_expected_matches(self):
        """Test expected matches for 1v2 mode."""
        # C(n, 1) * C(n-1, 2)
        assert calculate_expected_matches(3, team1_size=1, team2_size=2) == 3
        assert calculate_expected_matches(4, team1_size=1, team2_size=2) == 12

    def test_2v3_expected_matches(self):
        """Test expected matches for 2v3 mode."""
        # C(n, 2) * C(n-2, 3)
        assert calculate_expected_matches(5, team1_size=2, team2_size=3) == 10

    def test_below_minimum_returns_zero(self):
        """Test that below minimum players returns 0."""
        assert calculate_expected_matches(1, team1_size=1, team2_size=1) == 0
        assert calculate_expected_matches(3, team1_size=2, team2_size=2) == 0
        assert calculate_expected_matches(5, team1_size=3, team2_size=3) == 0
        assert calculate_expected_matches(2, team1_size=1, team2_size=2) == 0


class TestMultiRoundGeneration:
    """Tests for multi-round match generation."""

    def test_single_round_default(self, four_players):
        """Test that default is single round."""
        matches = generate_matches(four_players, shuffle=False)
        assert len(matches) == 3
        assert all(m.round == 1 for m in matches)

    def test_multiple_rounds(self, four_players):
        """Test generating multiple rounds."""
        matches = generate_matches(four_players, shuffle=False, num_rounds=3)
        # 4 players = 3 matches per round, 3 rounds = 9 matches
        assert len(matches) == 9

    def test_round_numbers_correct(self, four_players):
        """Test that round numbers are assigned correctly."""
        matches = generate_matches(four_players, shuffle=False, num_rounds=3)
        round1 = [m for m in matches if m.round == 1]
        round2 = [m for m in matches if m.round == 2]
        round3 = [m for m in matches if m.round == 3]
        assert len(round1) == 3
        assert len(round2) == 3
        assert len(round3) == 3

    def test_start_round_parameter(self, four_players):
        """Test start_round parameter for adding rounds."""
        matches = generate_matches(four_players, shuffle=False, num_rounds=2, start_round=3)
        assert all(m.round in [3, 4] for m in matches)
        round3 = [m for m in matches if m.round == 3]
        round4 = [m for m in matches if m.round == 4]
        assert len(round3) == 3
        assert len(round4) == 3

    def test_start_id_parameter(self, four_players):
        """Test start_id parameter for adding rounds."""
        matches = generate_matches(four_players, shuffle=False, num_rounds=2, start_id=10)
        ids = [m.id for m in matches]
        assert ids == list(range(10, 16))  # 6 matches starting at ID 10

    def test_combined_start_parameters(self, four_players):
        """Test combining start_id and start_round."""
        matches = generate_matches(
            four_players, shuffle=False, num_rounds=2, start_id=7, start_round=2
        )
        assert len(matches) == 6
        assert matches[0].id == 7
        assert matches[-1].id == 12
        assert matches[0].round == 2
        assert matches[5].round == 3

    def test_1v2_multiple_rounds(self, three_players):
        """Test multiple rounds with asymmetric 1v2 mode."""
        matches = generate_matches(
            three_players, team1_size=1, team2_size=2, shuffle=False, num_rounds=2
        )
        # 3 players in 1v2 = 3 matches per round, 2 rounds = 6 matches
        assert len(matches) == 6

    def test_1v1_multiple_rounds(self, three_players):
        """Test multiple rounds with 1v1 mode."""
        matches = generate_matches(
            three_players, team1_size=1, team2_size=1, shuffle=False, num_rounds=3
        )
        # 3 players in 1v1 = 3 matches per round, 3 rounds = 9 matches
        assert len(matches) == 9

    def test_each_round_has_same_matchups(self, four_players):
        """Test that each round contains the same matchups."""
        matches = generate_matches(four_players, shuffle=False, num_rounds=2)

        round1 = [m for m in matches if m.round == 1]
        round2 = [m for m in matches if m.round == 2]

        # Create normalized sets of matchups
        def match_key(m):
            t1 = tuple(sorted(m.team1))
            t2 = tuple(sorted(m.team2))
            return tuple(sorted([t1, t2]))

        round1_keys = {match_key(m) for m in round1}
        round2_keys = {match_key(m) for m in round2}

        assert round1_keys == round2_keys


class TestGetSittingOut:
    """Tests for get_sitting_out function."""

    def test_sitting_out_5_players_2v2(self, five_players):
        """Test identifying sitting out player with 5 players in 2v2."""
        matches = generate_matches(five_players, shuffle=False)
        # Check that exactly one player sits out each match
        for match in matches:
            sitting = get_sitting_out(match, five_players)
            assert len(sitting) == 1
            # Sitting out player should not be in either team
            assert sitting[0] not in match.team1
            assert sitting[0] not in match.team2

    def test_sitting_out_6_players_2v2(self):
        """Test identifying sitting out players with 6 players in 2v2."""
        players = ["A", "B", "C", "D", "E", "F"]
        matches = generate_matches(players, shuffle=False)
        # Check that exactly two players sit out each match
        for match in matches:
            sitting = get_sitting_out(match, players)
            assert len(sitting) == 2
            for p in sitting:
                assert p not in match.team1
                assert p not in match.team2

    def test_sitting_out_4_players_2v2(self, four_players):
        """Test that no one sits out with 4 players in 2v2."""
        matches = generate_matches(four_players, shuffle=False)
        for match in matches:
            sitting = get_sitting_out(match, four_players)
            assert len(sitting) == 0

    def test_sitting_out_3_players_1v1(self, three_players):
        """Test identifying sitting out player with 3 players in 1v1."""
        matches = generate_matches(three_players, team1_size=1, team2_size=1, shuffle=False)
        for match in matches:
            sitting = get_sitting_out(match, three_players)
            assert len(sitting) == 1
            assert sitting[0] not in match.team1
            assert sitting[0] not in match.team2

    def test_sitting_out_sorted(self):
        """Test that sitting out players are returned sorted."""
        players = ["Zoe", "Alice", "Bob", "Charlie", "Dave"]
        matches = generate_matches(players, shuffle=False)
        for match in matches:
            sitting = get_sitting_out(match, players)
            assert sitting == tuple(sorted(sitting))


class TestOptimizeMatchOrder:
    """Tests for optimize_match_order function."""

    def test_no_consecutive_sitouts_5_players(self, five_players):
        """Test that 5-player 2v2 has no consecutive sit-outs."""
        matches = generate_matches(five_players, shuffle=True)

        for i in range(len(matches) - 1):
            current_sitting = set(get_sitting_out(matches[i], five_players))
            next_sitting = set(get_sitting_out(matches[i + 1], five_players))
            # No overlap between consecutive sit-outs
            overlap = current_sitting & next_sitting
            assert len(overlap) == 0, f"Match {i} and {i+1} both have {overlap} sitting out"

    def test_no_consecutive_sitouts_6_players(self):
        """Test that 6-player 2v2 has no consecutive sit-outs."""
        players = ["A", "B", "C", "D", "E", "F"]
        matches = generate_matches(players, shuffle=True)

        for i in range(len(matches) - 1):
            current_sitting = set(get_sitting_out(matches[i], players))
            next_sitting = set(get_sitting_out(matches[i + 1], players))
            overlap = current_sitting & next_sitting
            assert len(overlap) == 0, f"Match {i} and {i+1} both have {overlap} sitting out"

    def test_even_distribution_5_players(self, five_players):
        """Test that sit-outs are evenly distributed for 5 players."""
        matches = generate_matches(five_players, shuffle=True)

        sit_out_counts = {p: 0 for p in five_players}
        for match in matches:
            sitting = get_sitting_out(match, five_players)
            for p in sitting:
                sit_out_counts[p] += 1

        # With 15 matches and 5 players, each player sits out 3 matches
        # Each match, 1 player sits out, so total sit-outs = 15
        # Evenly distributed = 15 / 5 = 3 per player
        counts = list(sit_out_counts.values())
        assert max(counts) - min(counts) <= 1, f"Uneven distribution: {sit_out_counts}"

    def test_even_distribution_6_players(self):
        """Test that sit-outs are evenly distributed for 6 players."""
        players = ["A", "B", "C", "D", "E", "F"]
        matches = generate_matches(players, shuffle=True)

        sit_out_counts = {p: 0 for p in players}
        for match in matches:
            sitting = get_sitting_out(match, players)
            for p in sitting:
                sit_out_counts[p] += 1

        # With 45 matches and 6 players, each match has 2 sitting out
        # Total sit-outs = 45 * 2 = 90
        # Evenly distributed = 90 / 6 = 15 per player
        counts = list(sit_out_counts.values())
        assert max(counts) - min(counts) <= 1, f"Uneven distribution: {sit_out_counts}"

    def test_4_players_no_optimization_needed(self, four_players):
        """Test that 4 players (no one sits out) works correctly."""
        matches = generate_matches(four_players, shuffle=True)
        # Should return same number of matches
        assert len(matches) == 3

    def test_optimize_preserves_all_matches(self, five_players):
        """Test that optimization preserves all matches."""
        unoptimized = generate_matches(five_players, shuffle=False)
        optimized = generate_matches(five_players, shuffle=True)

        # Same number of matches
        assert len(unoptimized) == len(optimized)

        # Same set of matchups
        def match_key(m):
            t1 = tuple(sorted(m.team1))
            t2 = tuple(sorted(m.team2))
            return tuple(sorted([t1, t2]))

        unoptimized_keys = {match_key(m) for m in unoptimized}
        optimized_keys = {match_key(m) for m in optimized}
        assert unoptimized_keys == optimized_keys

    def test_1v1_no_consecutive_sitouts(self, three_players):
        """Test 1v1 with 3 players has no consecutive sit-outs."""
        matches = generate_matches(three_players, team1_size=1, team2_size=1, shuffle=True)

        for i in range(len(matches) - 1):
            current_sitting = set(get_sitting_out(matches[i], three_players))
            next_sitting = set(get_sitting_out(matches[i + 1], three_players))
            overlap = current_sitting & next_sitting
            assert len(overlap) == 0, f"Match {i} and {i+1} both have {overlap} sitting out"

    def test_empty_matches_list(self, five_players):
        """Test that empty list returns empty list."""
        result = optimize_match_order([], five_players)
        assert result == []

    def test_ids_are_sequential(self, five_players):
        """Test that IDs remain sequential after optimization."""
        matches = generate_matches(five_players, shuffle=True)
        ids = [m.id for m in matches]
        assert ids == list(range(1, len(matches) + 1))
