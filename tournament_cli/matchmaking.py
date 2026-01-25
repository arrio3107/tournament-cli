"""Match generation logic for 2v2 tournaments."""

import random
from itertools import combinations
from tournament_cli.models import Match


def generate_matches(player_names: list[str], shuffle: bool = True) -> list[Match]:
    """
    Generate all valid 2v2 matchups where:
    - Every player plays WITH every other player as teammates
    - Every player plays AGAINST every other player as opponents

    For n players: Total matches = n(n-1)(n-2)(n-3) / 8

    Args:
        player_names: List of player names
        shuffle: If True, randomize the match order
    """
    if len(player_names) < 4:
        raise ValueError("Need at least 4 players for a 2v2 tournament")

    # Generate all possible 2-player teams
    all_teams = list(combinations(player_names, 2))

    # Generate all valid matchups (teams with no overlapping players)
    matchups = []
    seen_matchups = set()

    for i, team1 in enumerate(all_teams):
        for team2 in all_teams[i + 1:]:
            # Check for player overlap
            if set(team1) & set(team2):
                continue

            # Create a normalized key to avoid duplicates
            # Sort teams and players within teams for consistent ordering
            t1_sorted = tuple(sorted(team1))
            t2_sorted = tuple(sorted(team2))
            matchup_key = tuple(sorted([t1_sorted, t2_sorted]))

            if matchup_key not in seen_matchups:
                seen_matchups.add(matchup_key)
                matchups.append((team1, team2))

    # Shuffle the matchups for variety
    if shuffle:
        random.shuffle(matchups)

    # Create Match objects with sequential IDs
    matches = [
        Match(id=i + 1, team1=team1, team2=team2)
        for i, (team1, team2) in enumerate(matchups)
    ]

    return matches


def calculate_expected_matches(num_players: int) -> int:
    """Calculate the expected number of matches for n players."""
    if num_players < 4:
        return 0
    n = num_players
    return (n * (n - 1) * (n - 2) * (n - 3)) // 8
