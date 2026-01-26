"""Match generation logic for tournaments with variable team sizes."""

import random
from itertools import combinations
from math import comb
from typing import List, Tuple
from tournament_cli.models import Match


def get_sitting_out(match: Match, all_players: List[str]) -> Tuple[str, ...]:
    """Return tuple of players not in this match, sorted alphabetically."""
    playing = set(match.team1) | set(match.team2)
    return tuple(sorted(set(all_players) - playing))


def optimize_match_order(matches: List[Match], all_players: List[str]) -> List[Match]:
    """Reorder matches to minimize consecutive sit-outs and distribute breaks evenly.

    Uses a greedy algorithm that:
    1. Avoids having the same player sit out twice in a row
    2. Prioritizes giving breaks to players who have sat out the least

    Args:
        matches: List of matches to reorder
        all_players: List of all player names

    Returns:
        Reordered list of matches
    """
    if not matches:
        return matches

    players_per_match = len(matches[0].team1) + len(matches[0].team2)
    if len(all_players) <= players_per_match:
        # No one sits out, any order works
        return matches

    # Greedy algorithm: avoid consecutive sit-outs
    remaining = list(matches)
    ordered = []
    last_sat_out: set = set()
    sit_out_counts = {p: 0 for p in all_players}

    while remaining:
        # Find candidates where no one from last_sat_out sits out again
        candidates = []
        for m in remaining:
            sitting = set(get_sitting_out(m, all_players))
            if not (sitting & last_sat_out):
                candidates.append(m)

        if not candidates:
            # Fallback: minimize overlap with last sitting out players
            candidates = remaining

        # Among candidates, prefer match where sitting players have highest debt
        # (i.e., they've sat out the least, so it's their turn to rest)
        def score(m: Match) -> int:
            sitting = get_sitting_out(m, all_players)
            return sum(sit_out_counts[p] for p in sitting)

        # Lower score = these players sat out less = give them a break
        selected = min(candidates, key=score)

        ordered.append(selected)
        remaining.remove(selected)

        sitting = get_sitting_out(selected, all_players)
        last_sat_out = set(sitting)
        for p in sitting:
            sit_out_counts[p] += 1

    return ordered


def get_minimum_players(team1_size: int, team2_size: int) -> int:
    """Return minimum players needed for this mode.

    For any mode, we need enough players to fill both teams without overlap.
    """
    return team1_size + team2_size


def generate_matches(
    player_names: list[str],
    team1_size: int = 2,
    team2_size: int = 2,
    shuffle: bool = True,
    num_rounds: int = 1,
    start_id: int = 1,
    start_round: int = 1
) -> list[Match]:
    """
    Generate all valid matchups for the given team sizes.

    For symmetric modes (NvN):
    - Every player plays WITH every other player as teammates (if team_size > 1)
    - Every player plays AGAINST every other player as opponents

    For asymmetric modes (NvM where N < M):
    - Every player takes turns in both team positions

    Args:
        player_names: List of player names
        team1_size: Number of players on team 1
        team2_size: Number of players on team 2
        shuffle: If True, randomize the match order
        num_rounds: Number of rounds to generate
        start_id: Starting match ID
        start_round: Starting round number

    Returns:
        List of Match objects
    """
    min_players = get_minimum_players(team1_size, team2_size)
    if len(player_names) < min_players:
        raise ValueError(
            f"Need at least {min_players} players for a {team1_size}v{team2_size} tournament"
        )

    if team1_size == team2_size:
        base_matchups = _generate_symmetric_matches(player_names, team1_size)
    else:
        base_matchups = _generate_asymmetric_matches(player_names, team1_size, team2_size)

    # Generate matches for each round
    matches = []
    current_id = start_id

    for round_num in range(start_round, start_round + num_rounds):
        # Create Match objects for this round first
        round_matches = []
        for team1, team2 in base_matchups:
            round_matches.append(Match(id=current_id, team1=team1, team2=team2, round=round_num))
            current_id += 1

        if shuffle:
            # Optimize match order to minimize consecutive sit-outs
            round_matches = optimize_match_order(round_matches, player_names)
            # Reassign sequential IDs after optimization
            for i, match in enumerate(round_matches):
                match.id = start_id + len(matches) + i

        matches.extend(round_matches)

    return matches


def _generate_symmetric_matches(
    player_names: list[str],
    team_size: int
) -> list[tuple]:
    """Generate matches for symmetric modes (NvN)."""
    if team_size == 1:
        # 1v1: every pair of players faces each other once
        matchups = []
        for p1, p2 in combinations(player_names, 2):
            matchups.append(((p1,), (p2,)))
        return matchups

    # For team_size >= 2: generate all team combinations and pair them
    all_teams = list(combinations(player_names, team_size))

    matchups = []
    seen_matchups = set()

    for i, team1 in enumerate(all_teams):
        for team2 in all_teams[i + 1:]:
            # Check for player overlap
            if set(team1) & set(team2):
                continue

            # Create a normalized key to avoid duplicates
            t1_sorted = tuple(sorted(team1))
            t2_sorted = tuple(sorted(team2))
            matchup_key = tuple(sorted([t1_sorted, t2_sorted]))

            if matchup_key not in seen_matchups:
                seen_matchups.add(matchup_key)
                matchups.append((team1, team2))

    return matchups


def _generate_asymmetric_matches(
    player_names: list[str],
    team1_size: int,
    team2_size: int
) -> list[tuple]:
    """Generate matches for asymmetric modes (NvM where N != M).

    In asymmetric modes, each player participates in both positions:
    - As part of the smaller team
    - As part of the larger team
    """
    smaller_size = min(team1_size, team2_size)
    larger_size = max(team1_size, team2_size)
    swap_order = team1_size > team2_size

    matchups = []
    seen_matchups = set()

    # Generate all smaller teams
    all_smaller_teams = list(combinations(player_names, smaller_size))
    # Generate all larger teams
    all_larger_teams = list(combinations(player_names, larger_size))

    for smaller_team in all_smaller_teams:
        for larger_team in all_larger_teams:
            # Check for player overlap
            if set(smaller_team) & set(larger_team):
                continue

            # Create a normalized key to avoid duplicates
            # For asymmetric matches, we need to track which is which
            small_sorted = tuple(sorted(smaller_team))
            large_sorted = tuple(sorted(larger_team))
            matchup_key = (small_sorted, large_sorted)

            if matchup_key not in seen_matchups:
                seen_matchups.add(matchup_key)
                if swap_order:
                    # team1_size > team2_size, so larger team is team1
                    matchups.append((larger_team, smaller_team))
                else:
                    # team1_size < team2_size, so smaller team is team1
                    matchups.append((smaller_team, larger_team))

    return matchups


def calculate_expected_matches(
    num_players: int,
    team1_size: int = 2,
    team2_size: int = 2
) -> int:
    """Calculate the expected number of matches for n players.

    For symmetric modes (NvN):
    - 1v1: C(n, 2) = n(n-1)/2
    - 2v2: C(n, 2) * C(n-2, 2) / 2 = n(n-1)(n-2)(n-3)/8
    - NvN: C(n, N) * C(n-N, N) / 2

    For asymmetric modes (NvM where N < M):
    - NvM: C(n, N) * C(n-N, M) where N < M
    """
    min_players = get_minimum_players(team1_size, team2_size)
    if num_players < min_players:
        return 0

    n = num_players

    if team1_size == team2_size:
        # Symmetric mode
        k = team1_size
        if k == 1:
            return comb(n, 2)
        # General formula: C(n, k) * C(n-k, k) / 2
        return (comb(n, k) * comb(n - k, k)) // 2
    else:
        # Asymmetric mode
        smaller = min(team1_size, team2_size)
        larger = max(team1_size, team2_size)
        # C(n, smaller) * C(n - smaller, larger)
        return comb(n, smaller) * comb(n - smaller, larger)
