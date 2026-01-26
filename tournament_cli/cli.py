"""Main CLI entry point and commands."""

import typer
from pathlib import Path
from typing import Optional
from rich.prompt import Prompt, IntPrompt

from tournament_cli.models import Tournament, Player
from tournament_cli.matchmaking import generate_matches, calculate_expected_matches, get_minimum_players
from tournament_cli.storage import (
    load_tournament,
    save_tournament,
    list_tournaments,
    get_current_tournament,
    set_current_tournament,
    save_current_tournament,
)
from tournament_cli.display import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    display_tournament_status,
    display_standings,
    display_schedule,
    display_match,
    display_player_stats,
    display_tournaments_list,
    display_teams,
    format_team,
)
from tournament_cli.export import export_tournament_markdown, save_markdown_export, export_tournament_pdf

app = typer.Typer(
    name="tournament-cli",
    help="Tournament Manager - Track standings, teams, and stats for 1v1, 2v2, 3v3, and asymmetric modes",
    add_completion=False,
)


def require_tournament() -> Tournament:
    """Get current tournament or exit with error."""
    tournament = get_current_tournament()
    if not tournament:
        print_error("No tournament loaded. Use 'tournament-cli load <name>' or 'tournament-cli new <name>' first.")
        raise typer.Exit(1)
    return tournament


def parse_mode(mode: str) -> tuple:
    """Parse mode string like '2v2' or '1v2' into (team1_size, team2_size)."""
    import re
    match = re.match(r'^(\d+)v(\d+)$', mode.lower())
    if not match:
        raise ValueError(f"Invalid mode format: '{mode}'. Use format like '1v1', '2v2', '1v2', etc.")

    team1_size = int(match.group(1))
    team2_size = int(match.group(2))

    if team1_size < 1 or team2_size < 1:
        raise ValueError("Team sizes must be at least 1")

    if team1_size > 10 or team2_size > 10:
        raise ValueError("Team sizes cannot exceed 10")

    return team1_size, team2_size


@app.command()
def new(
    name: str = typer.Argument(..., help="Tournament name"),
    mode: str = typer.Option(..., "--mode", "-m", help="Tournament mode (e.g., 1v1, 2v2, 3v3, 1v2)"),
    players_opt: Optional[str] = typer.Option(None, "--players", "-p", help="Comma-separated player names (e.g., 'Alice,Bob,Carol,Dave')"),
    rounds: int = typer.Option(1, "--rounds", "-r", help="Number of rounds to play")
):
    """Create a new tournament.

    Examples:
        tournament-cli new "Friday FIFA" -m 2v2
        tournament-cli new "Quick Match" -m 1v1 -p "Alice,Bob"
        tournament-cli new "Game Night" -m 2v2 -p "Alice,Bob,Carol,Dave" --rounds 2
    """
    # Parse mode
    try:
        team1_size, team2_size = parse_mode(mode)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    min_players = get_minimum_players(team1_size, team2_size)

    # Check if tournament already exists
    existing = load_tournament(name)
    if existing:
        overwrite = Prompt.ask(
            f"Tournament '{name}' already exists. Overwrite?",
            choices=["y", "n"],
            default="n"
        )
        if overwrite.lower() != "y":
            print_info("Cancelled.")
            raise typer.Exit(0)

    # Get player names from --players flag or interactive prompt
    if players_opt:
        # Parse comma-separated player names
        players = [p.strip() for p in players_opt.split(",") if p.strip()]

        # Check for duplicates
        seen = set()
        for p in players:
            if p.lower() in seen:
                print_error(f"Duplicate player name: '{p}'")
                raise typer.Exit(1)
            seen.add(p.lower())

        # Validate minimum players
        if len(players) < min_players:
            print_error(f"Need at least {min_players} players for {team1_size}v{team2_size}. Got {len(players)}.")
            raise typer.Exit(1)
    else:
        # Interactive prompt
        console.print(f"\n[bold]Enter player names[/bold] (minimum {min_players} players for {team1_size}v{team2_size})")
        console.print("[dim]Enter an empty name when done.[/dim]\n")

        players = []
        while True:
            player_num = len(players) + 1
            name_input = Prompt.ask(f"Player {player_num}", default="")

            if not name_input.strip():
                if len(players) < min_players:
                    print_warning(f"Need at least {min_players} players for {team1_size}v{team2_size}. Currently have {len(players)}.")
                    continue
                break

            # Check for duplicate names
            if name_input.strip().lower() in [p.lower() for p in players]:
                print_warning("Player name already exists. Please enter a different name.")
                continue

            players.append(name_input.strip())

    # Validate rounds
    if rounds < 1:
        print_error("Number of rounds must be at least 1.")
        raise typer.Exit(1)

    # Generate matches
    matches = generate_matches(players, team1_size=team1_size, team2_size=team2_size, num_rounds=rounds)
    expected = calculate_expected_matches(len(players), team1_size=team1_size, team2_size=team2_size)

    # Create tournament
    tournament = Tournament(
        name=name,
        players=[Player(name=p) for p in players],
        matches=matches,
        team1_size=team1_size,
        team2_size=team2_size,
    )

    # Save and set as current
    save_tournament(tournament)
    set_current_tournament(tournament)

    print_success(f"\nTournament '{name}' created! ({tournament.mode})")
    rounds_info = f" ({rounds} round{'s' if rounds > 1 else ''} × {expected} matches)" if rounds > 1 else f" (expected: {expected})"
    console.print(f"[dim]Players: {len(players)} | Matches: {len(matches)}{rounds_info}[/dim]")
    console.print("\n[dim]Use 'tournament-cli schedule' to see all matches.[/dim]")


@app.command("list")
def list_cmd():
    """List all saved tournaments."""
    tournaments = list_tournaments()
    display_tournaments_list(tournaments)


@app.command()
def load(name: str = typer.Argument(..., help="Tournament name")):
    """Load an existing tournament."""
    tournament = load_tournament(name)
    if not tournament:
        print_error(f"Tournament '{name}' not found.")
        raise typer.Exit(1)

    set_current_tournament(tournament)
    print_success(f"Loaded tournament '{name}'")
    display_tournament_status(tournament)


@app.command()
def status():
    """Show current tournament overview."""
    tournament = require_tournament()
    display_tournament_status(tournament)


@app.command()
def schedule(
    all: bool = typer.Option(True, "--all/--remaining", "-a/-r", help="Show all matches or only remaining"),
    round_num: Optional[int] = typer.Option(None, "--round", help="Filter by round number")
):
    """Show match schedule."""
    tournament = require_tournament()
    display_schedule(tournament, show_all=all, round_filter=round_num)


@app.command()
def play(
    match_id: Optional[int] = typer.Argument(None, help="Match ID (optional, defaults to next unplayed)")
):
    """Record a match result."""
    tournament = require_tournament()

    # Get the match to play
    if match_id is not None:
        match = tournament.get_match_by_id(match_id)
        if not match:
            print_error(f"Match #{match_id} not found.")
            raise typer.Exit(1)
        if match.played:
            replay = Prompt.ask(
                f"Match #{match_id} already played ({match.score1}-{match.score2}). Update result?",
                choices=["y", "n"],
                default="n"
            )
            if replay.lower() != "y":
                raise typer.Exit(0)
            # Reverse the previous stats
            _reverse_match_stats(tournament, match)
    else:
        match = tournament.get_next_match()
        if not match:
            print_success("All matches have been played!")
            raise typer.Exit(0)

    # Display the match
    display_match(match)

    # Get scores
    console.print()
    team1_str = format_team(match.team1)
    team2_str = format_team(match.team2)

    score1 = IntPrompt.ask(f"Score for [cyan]{team1_str}[/cyan]")
    score2 = IntPrompt.ask(f"Score for [magenta]{team2_str}[/magenta]")

    if score1 < 0 or score2 < 0:
        print_error("Scores cannot be negative.")
        raise typer.Exit(1)

    # Update match
    match.score1 = score1
    match.score2 = score2

    # Update player stats
    _update_player_stats(tournament, match)

    # Save
    save_current_tournament()

    # Display result
    console.print()
    if match.is_draw:
        print_info(f"Draw! {score1} - {score2}")
    else:
        winner = match.winner
        winner_str = format_team(winner)
        print_success(f"{winner_str} win {max(score1, score2)} - {min(score1, score2)}!")

    # Show remaining
    remaining = tournament.remaining_matches
    if remaining > 0:
        console.print(f"\n[dim]{remaining} matches remaining[/dim]")
    else:
        console.print("\n[bold green]Tournament complete![/bold green]")
        display_standings(tournament)


def _update_player_stats(tournament: Tournament, match: 'Match') -> None:
    """Update player statistics after a match."""
    team1_players = [tournament.get_player(name) for name in match.team1]
    team2_players = [tournament.get_player(name) for name in match.team2]

    if match.is_draw:
        # Draw - 1 point each, goals split evenly (conceptually)
        for player in team1_players + team2_players:
            if player:
                player.stats.draws += 1
                # For draws, attribute goals to all players
                if player in team1_players:
                    player.stats.goals_scored += match.score1
                    player.stats.goals_conceded += match.score2
                else:
                    player.stats.goals_scored += match.score2
                    player.stats.goals_conceded += match.score1
    else:
        # Win/Loss
        winners = team1_players if match.score1 > match.score2 else team2_players
        losers = team2_players if match.score1 > match.score2 else team1_players
        winner_goals = max(match.score1, match.score2)
        loser_goals = min(match.score1, match.score2)

        for player in winners:
            if player:
                player.stats.wins += 1
                player.stats.goals_scored += winner_goals
                player.stats.goals_conceded += loser_goals

        for player in losers:
            if player:
                player.stats.losses += 1
                player.stats.goals_scored += loser_goals
                player.stats.goals_conceded += winner_goals


def _reverse_match_stats(tournament: Tournament, match: 'Match') -> None:
    """Reverse player statistics for a match (when re-recording)."""
    if not match.played:
        return

    team1_players = [tournament.get_player(name) for name in match.team1]
    team2_players = [tournament.get_player(name) for name in match.team2]

    if match.is_draw:
        for player in team1_players + team2_players:
            if player:
                player.stats.draws -= 1
                if player in team1_players:
                    player.stats.goals_scored -= match.score1
                    player.stats.goals_conceded -= match.score2
                else:
                    player.stats.goals_scored -= match.score2
                    player.stats.goals_conceded -= match.score1
    else:
        winners = team1_players if match.score1 > match.score2 else team2_players
        losers = team2_players if match.score1 > match.score2 else team1_players
        winner_goals = max(match.score1, match.score2)
        loser_goals = min(match.score1, match.score2)

        for player in winners:
            if player:
                player.stats.wins -= 1
                player.stats.goals_scored -= winner_goals
                player.stats.goals_conceded -= loser_goals

        for player in losers:
            if player:
                player.stats.losses -= 1
                player.stats.goals_scored -= loser_goals
                player.stats.goals_conceded -= winner_goals


@app.command()
def standings():
    """Show player rankings."""
    tournament = require_tournament()
    display_standings(tournament)


@app.command()
def teams():
    """Show best team pairings."""
    tournament = require_tournament()
    display_teams(tournament)


@app.command()
def stats(player: str = typer.Argument(..., help="Player name")):
    """Show detailed player statistics."""
    tournament = require_tournament()

    player_obj = tournament.get_player(player)
    if not player_obj:
        print_error(f"Player '{player}' not found.")
        console.print("[dim]Available players: " + ", ".join(p.name for p in tournament.players) + "[/dim]")
        raise typer.Exit(1)

    display_player_stats(player_obj, tournament)


@app.command("add-round")
def add_round(
    count: int = typer.Argument(1, help="Number of rounds to add")
):
    """Add additional round(s) of matches to current tournament."""
    tournament = require_tournament()

    if count < 1:
        print_error("Number of rounds to add must be at least 1.")
        raise typer.Exit(1)

    current_rounds = tournament.current_round_count
    next_round = current_rounds + 1
    next_id = max(m.id for m in tournament.matches) + 1

    player_names = [p.name for p in tournament.players]
    new_matches = generate_matches(
        player_names,
        team1_size=tournament.team1_size,
        team2_size=tournament.team2_size,
        num_rounds=count,
        start_id=next_id,
        start_round=next_round
    )

    tournament.matches.extend(new_matches)
    save_current_tournament()

    matches_per_round = tournament.matches_per_round
    print_success(f"Added {count} round{'s' if count > 1 else ''} with {len(new_matches)} matches")
    console.print(f"[dim]Tournament now has {tournament.current_round_count} rounds ({tournament.total_matches} total matches)[/dim]")


@app.command()
def reset():
    """Reset all match results."""
    tournament = require_tournament()

    confirm = Prompt.ask(
        f"[red]Reset all {tournament.played_matches} match results for '{tournament.name}'?[/red]",
        choices=["y", "n"],
        default="n"
    )

    if confirm.lower() != "y":
        print_info("Cancelled.")
        raise typer.Exit(0)

    # Reset all matches
    for match in tournament.matches:
        match.score1 = None
        match.score2 = None

    # Reset all player stats
    for player in tournament.players:
        player.stats.wins = 0
        player.stats.draws = 0
        player.stats.losses = 0
        player.stats.goals_scored = 0
        player.stats.goals_conceded = 0

    save_current_tournament()
    print_success(f"Tournament '{tournament.name}' has been reset.")


@app.command()
def tui():
    """Launch interactive TUI mode.

    Opens a full-screen terminal interface with keyboard navigation for managing
    the current tournament. Requires a tournament to be loaded first.

    Keyboard shortcuts:
        m: Focus matches panel
        s: Focus standings panel
        i: Focus score input
        Tab: Cycle between panels
        j/k or arrows: Navigate up/down
        Enter: Context-sensitive action
        n: Jump to next unplayed match
        r: Refresh from disk
        q: Quit
    """
    from tournament_cli.tui import main as tui_main
    tui_main()


@app.command()
def export(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    pdf: bool = typer.Option(False, "--pdf", "-p", help="Export as PDF instead of Markdown"),
):
    """Export tournament to Markdown or PDF."""
    tournament = require_tournament()

    if pdf:
        # PDF export
        path = export_tournament_pdf(tournament, output)
        print_success(f"Exported PDF to {path}")
    else:
        # Markdown export
        path = save_markdown_export(tournament, output)
        print_success(f"Exported Markdown to {path}")

        # Show preview for markdown
        console.print("\n[dim]Preview:[/dim]")
        content = export_tournament_markdown(tournament)
        preview_lines = content.split("\n")[:20]
        for line in preview_lines:
            console.print(f"[dim]{line}[/dim]")
        if len(content.split("\n")) > 20:
            console.print("[dim]...[/dim]")


if __name__ == "__main__":
    app()
