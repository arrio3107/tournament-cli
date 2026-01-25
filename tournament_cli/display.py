"""Rich formatting and display utilities."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from tournament_cli.models import Tournament, Player, Match


console = Console()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error: {message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]{message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]{message}[/cyan]")


def display_tournament_status(tournament: Tournament) -> None:
    """Display tournament overview."""
    # Header panel
    header = Text()
    header.append(f"{tournament.name}\n", style="bold cyan")
    header.append(f"Players: {len(tournament.players)} | ", style="dim")
    header.append(f"Matches: {tournament.played_matches}/{tournament.total_matches}")

    console.print(Panel(header, title="Tournament Status", border_style="cyan"))

    # Progress bar
    console.print()
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Progress", total=tournament.total_matches)
        progress.update(task, completed=tournament.played_matches)

    # Players list
    console.print()
    console.print("[bold]Players:[/bold]", ", ".join(p.name for p in tournament.players))


def display_standings(tournament: Tournament) -> None:
    """Display player rankings table."""
    table = Table(title=f"{tournament.name} - Standings", border_style="cyan")

    table.add_column("#", justify="center", style="dim", width=4)
    table.add_column("Player", style="bold")
    table.add_column("P", justify="center")  # Played
    table.add_column("W", justify="center", style="green")
    table.add_column("D", justify="center", style="yellow")
    table.add_column("L", justify="center", style="red")
    table.add_column("GF", justify="center")  # Goals For
    table.add_column("GA", justify="center")  # Goals Against
    table.add_column("GD", justify="center")  # Goal Difference
    table.add_column("Pts", justify="center", style="bold cyan")
    table.add_column("Win%", justify="center")

    # Sort players by points, then goal difference, then goals scored
    sorted_players = sorted(
        tournament.players,
        key=lambda p: (p.stats.points, p.stats.goal_difference, p.stats.goals_scored),
        reverse=True
    )

    medals = ["[yellow]1[/yellow]", "[white]2[/white]", "[rgb(205,127,50)]3[/rgb(205,127,50)]"]

    for i, player in enumerate(sorted_players, 1):
        s = player.stats
        rank = medals[i - 1] if i <= 3 else str(i)

        gd = s.goal_difference
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        gd_style = "green" if gd > 0 else ("red" if gd < 0 else "")

        table.add_row(
            rank,
            player.name,
            str(s.games_played),
            str(s.wins),
            str(s.draws),
            str(s.losses),
            str(s.goals_scored),
            str(s.goals_conceded),
            f"[{gd_style}]{gd_str}[/{gd_style}]" if gd_style else gd_str,
            str(s.points),
            f"{s.win_rate:.0f}%",
        )

    console.print(table)


def display_schedule(tournament: Tournament, show_all: bool = True) -> None:
    """Display match schedule."""
    table = Table(title=f"{tournament.name} - Schedule", border_style="cyan")

    table.add_column("ID", justify="center", style="dim", width=4)
    table.add_column("Status", justify="center", width=6)
    table.add_column("Team 1", style="cyan")
    table.add_column("Score", justify="center", width=7)
    table.add_column("Team 2", style="magenta")

    for match in tournament.matches:
        if not show_all and match.played:
            continue

        status = "[green]Done[/green]" if match.played else "[yellow]Pend[/yellow]"
        team1_str = f"{match.team1[0]} & {match.team1[1]}"
        team2_str = f"{match.team2[0]} & {match.team2[1]}"

        if match.played:
            score_str = f"{match.score1} - {match.score2}"
        else:
            score_str = "- vs -"

        table.add_row(
            str(match.id),
            status,
            team1_str,
            score_str,
            team2_str,
        )

    console.print(table)

    # Summary
    console.print()
    console.print(
        f"[dim]Played: {tournament.played_matches} | "
        f"Remaining: {tournament.remaining_matches} | "
        f"Total: {tournament.total_matches}[/dim]"
    )


def display_match(match: Match) -> None:
    """Display a single match."""
    team1_str = f"{match.team1[0]} & {match.team1[1]}"
    team2_str = f"{match.team2[0]} & {match.team2[1]}"

    content = Text()
    content.append(f"Match #{match.id}\n\n", style="bold")
    content.append(team1_str, style="cyan")
    content.append("  vs  ", style="dim")
    content.append(team2_str, style="magenta")

    console.print(Panel(content, border_style="yellow"))


def display_player_stats(player: Player, tournament: Tournament) -> None:
    """Display detailed statistics for a player."""
    s = player.stats

    # Basic stats panel
    stats_text = Text()
    stats_text.append(f"Games Played: {s.games_played}\n")
    stats_text.append(f"Record: ", style="dim")
    stats_text.append(f"{s.wins}W ", style="green")
    stats_text.append(f"{s.draws}D ", style="yellow")
    stats_text.append(f"{s.losses}L\n", style="red")
    stats_text.append(f"Points: {s.points}\n", style="bold cyan")
    stats_text.append(f"Win Rate: {s.win_rate:.1f}%\n")
    stats_text.append(f"\nGoals Scored: {s.goals_scored}\n")
    stats_text.append(f"Goals Conceded: {s.goals_conceded}\n")
    gd = s.goal_difference
    gd_style = "green" if gd > 0 else ("red" if gd < 0 else "white")
    stats_text.append(f"Goal Difference: ", style="dim")
    stats_text.append(f"{'+' if gd > 0 else ''}{gd}", style=gd_style)

    console.print(Panel(stats_text, title=f"[bold]{player.name}[/bold]", border_style="cyan"))

    # Partnership stats
    partnership_stats = calculate_partnership_stats(player.name, tournament)
    if partnership_stats:
        partner_table = Table(title="Partnership Stats", border_style="dim")
        partner_table.add_column("Partner")
        partner_table.add_column("P", justify="center")
        partner_table.add_column("W", justify="center", style="green")
        partner_table.add_column("D", justify="center", style="yellow")
        partner_table.add_column("L", justify="center", style="red")
        partner_table.add_column("Win%", justify="center")

        for partner, stats in sorted(partnership_stats.items(), key=lambda x: x[1]["wins"], reverse=True):
            total = stats["wins"] + stats["draws"] + stats["losses"]
            win_rate = (stats["wins"] / total * 100) if total > 0 else 0
            partner_table.add_row(
                partner,
                str(total),
                str(stats["wins"]),
                str(stats["draws"]),
                str(stats["losses"]),
                f"{win_rate:.0f}%",
            )

        console.print()
        console.print(partner_table)


def calculate_partnership_stats(player_name: str, tournament: Tournament) -> dict:
    """Calculate stats for each teammate pairing."""
    stats = {}

    for match in tournament.matches:
        if not match.played:
            continue

        partner = None
        is_team1 = False

        if player_name in match.team1:
            partner = match.team1[0] if match.team1[1] == player_name else match.team1[1]
            is_team1 = True
        elif player_name in match.team2:
            partner = match.team2[0] if match.team2[1] == player_name else match.team2[1]
            is_team1 = False
        else:
            continue

        if partner not in stats:
            stats[partner] = {"wins": 0, "draws": 0, "losses": 0}

        if match.is_draw:
            stats[partner]["draws"] += 1
        elif (is_team1 and match.score1 > match.score2) or (not is_team1 and match.score2 > match.score1):
            stats[partner]["wins"] += 1
        else:
            stats[partner]["losses"] += 1

    return stats


def display_tournaments_list(tournaments: list[str]) -> None:
    """Display list of saved tournaments."""
    if not tournaments:
        print_warning("No tournaments found.")
        return

    table = Table(title="Saved Tournaments", border_style="cyan")
    table.add_column("#", justify="center", style="dim", width=4)
    table.add_column("Name")

    for i, name in enumerate(tournaments, 1):
        table.add_row(str(i), name)

    console.print(table)


def calculate_team_stats(tournament: Tournament) -> list[dict]:
    """Calculate statistics for each unique team pairing."""
    team_stats = {}

    for match in tournament.matches:
        if not match.played:
            continue

        # Process both teams
        for team, goals_for, goals_against in [
            (match.team1, match.score1, match.score2),
            (match.team2, match.score2, match.score1),
        ]:
            # Create a consistent team key (sorted names)
            team_key = tuple(sorted(team))

            if team_key not in team_stats:
                team_stats[team_key] = {
                    "players": team_key,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                }

            team_stats[team_key]["goals_for"] += goals_for
            team_stats[team_key]["goals_against"] += goals_against

            if goals_for > goals_against:
                team_stats[team_key]["wins"] += 1
            elif goals_for < goals_against:
                team_stats[team_key]["losses"] += 1
            else:
                team_stats[team_key]["draws"] += 1

    # Convert to list and add computed fields
    result = []
    for team_key, stats in team_stats.items():
        stats["games"] = stats["wins"] + stats["draws"] + stats["losses"]
        stats["points"] = stats["wins"] * 3 + stats["draws"]
        stats["goal_diff"] = stats["goals_for"] - stats["goals_against"]
        stats["win_rate"] = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0
        result.append(stats)

    # Sort by points, then goal difference, then goals scored
    result.sort(key=lambda x: (x["points"], x["goal_diff"], x["goals_for"]), reverse=True)

    return result


def display_teams(tournament: Tournament) -> None:
    """Display team rankings table."""
    table = Table(title=f"{tournament.name} - Best Teams", border_style="cyan")

    table.add_column("#", justify="center", style="dim", width=4)
    table.add_column("Team", style="bold")
    table.add_column("P", justify="center")
    table.add_column("W", justify="center", style="green")
    table.add_column("D", justify="center", style="yellow")
    table.add_column("L", justify="center", style="red")
    table.add_column("GF", justify="center")
    table.add_column("GA", justify="center")
    table.add_column("GD", justify="center")
    table.add_column("Pts", justify="center", style="bold cyan")
    table.add_column("Win%", justify="center")

    team_stats = calculate_team_stats(tournament)
    medals = ["[yellow]1[/yellow]", "[white]2[/white]", "[rgb(205,127,50)]3[/rgb(205,127,50)]"]

    for i, stats in enumerate(team_stats, 1):
        rank = medals[i - 1] if i <= 3 else str(i)
        team_name = f"{stats['players'][0]} & {stats['players'][1]}"

        gd = stats["goal_diff"]
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        gd_style = "green" if gd > 0 else ("red" if gd < 0 else "")

        table.add_row(
            rank,
            team_name,
            str(stats["games"]),
            str(stats["wins"]),
            str(stats["draws"]),
            str(stats["losses"]),
            str(stats["goals_for"]),
            str(stats["goals_against"]),
            f"[{gd_style}]{gd_str}[/{gd_style}]" if gd_style else gd_str,
            str(stats["points"]),
            f"{stats['win_rate']:.0f}%",
        )

    console.print(table)
