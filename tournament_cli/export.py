"""Markdown and PDF export functionality for tournaments."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from tournament_cli.models import Tournament, Player
from tournament_cli.display import calculate_partnership_stats, calculate_team_stats, format_team
from tournament_cli.matchmaking import get_sitting_out


# CSS styling for PDF export
PDF_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #333;
}

h1 {
    color: #1a5f2a;
    border-bottom: 3px solid #1a5f2a;
    padding-bottom: 10px;
    margin-bottom: 5px;
}

h2 {
    color: #2d7a3e;
    border-bottom: 1px solid #ccc;
    padding-bottom: 5px;
    margin-top: 25px;
    page-break-before: always;
}

h2:first-of-type {
    page-break-before: avoid;
}

h3 {
    color: #444;
    margin-top: 20px;
    margin-bottom: 10px;
    page-break-after: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10pt;
    page-break-inside: auto;
}

tr {
    page-break-inside: avoid;
    page-break-after: auto;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px 10px;
    text-align: left;
}

th {
    background-color: #1a5f2a;
    color: white;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

tr:hover {
    background-color: #e8f5e9;
}

td:first-child {
    text-align: center;
    font-weight: bold;
}

strong {
    color: #1a5f2a;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 20px 0;
}

ul {
    margin: 10px 0;
    padding-left: 20px;
}

li {
    margin: 5px 0;
}

em {
    color: #666;
    font-size: 9pt;
}

p {
    margin: 10px 0;
}

/* Medal colors */
.medal-gold { color: #ffd700; }
.medal-silver { color: #c0c0c0; }
.medal-bronze { color: #cd7f32; }
"""


def export_tournament_markdown(tournament: Tournament) -> str:
    """Export the entire tournament to Markdown format."""
    lines = []

    # Header
    lines.append(f"# {tournament.name}")
    lines.append("")
    header_parts = [
        f"**Mode:** {tournament.mode}",
        f"**Players:** {len(tournament.players)}",
    ]
    round_count = tournament.current_round_count
    if round_count > 1:
        header_parts.append(f"**Rounds:** {round_count}")
    header_parts.extend([
        f"**Matches:** {tournament.played_matches}/{tournament.total_matches}",
        f"**Progress:** {tournament.completion_percentage:.0f}%"
    ])
    lines.append(" | ".join(header_parts))
    lines.append("")
    lines.append(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    # Standings
    lines.append("---")
    lines.append("")
    lines.append("## Standings")
    lines.append("")
    lines.extend(_export_standings(tournament))
    lines.append("")

    # Best Teams (skip for 1v1)
    if not (tournament.team1_size == 1 and tournament.team2_size == 1):
        lines.append("---")
        lines.append("")
        lines.append("## Best Teams")
        lines.append("")
        lines.extend(_export_teams(tournament))
        lines.append("")

    # Schedule
    lines.append("---")
    lines.append("")
    lines.append("## Schedule")
    lines.append("")
    lines.extend(_export_schedule(tournament))
    lines.append("")

    # Player Stats
    lines.append("---")
    lines.append("")
    lines.append("## Player Statistics")
    lines.append("")
    for player in sorted(tournament.players, key=lambda p: p.stats.points, reverse=True):
        lines.extend(_export_player_stats(player, tournament))
        lines.append("")

    return "\n".join(lines)


def _export_standings(tournament: Tournament) -> list[str]:
    """Export standings table as Markdown."""
    lines = []

    # Sort players by points, goal difference, goals scored
    sorted_players = sorted(
        tournament.players,
        key=lambda p: (p.stats.points, p.stats.goal_difference, p.stats.goals_scored),
        reverse=True
    )

    # Table header
    lines.append("| # | Player | P | W | D | L | GF | GA | GD | Pts | Win% |")
    lines.append("|:-:|--------|:-:|:-:|:-:|:-:|:--:|:--:|:--:|:---:|:----:|")

    medals = ["🥇", "🥈", "🥉"]

    for i, player in enumerate(sorted_players, 1):
        s = player.stats
        rank = medals[i - 1] if i <= 3 else str(i)

        gd = s.goal_difference
        gd_str = f"+{gd}" if gd > 0 else str(gd)

        lines.append(
            f"| {rank} | **{player.name}** | {s.games_played} | {s.wins} | "
            f"{s.draws} | {s.losses} | {s.goals_scored} | {s.goals_conceded} | "
            f"{gd_str} | **{s.points}** | {s.win_rate:.0f}% |"
        )

    return lines


def _export_teams(tournament: Tournament) -> list[str]:
    """Export team rankings table as Markdown."""
    lines = []

    team_stats = calculate_team_stats(tournament)

    if not team_stats:
        lines.append("*No matches played yet.*")
        return lines

    # Table header
    lines.append("| # | Team | P | W | D | L | GF | GA | GD | Pts | Win% |")
    lines.append("|:-:|------|:-:|:-:|:-:|:-:|:--:|:--:|:--:|:---:|:----:|")

    medals = ["🥇", "🥈", "🥉"]

    for i, stats in enumerate(team_stats, 1):
        rank = medals[i - 1] if i <= 3 else str(i)
        team_name = format_team(stats['players'])

        gd = stats["goal_diff"]
        gd_str = f"+{gd}" if gd > 0 else str(gd)

        lines.append(
            f"| {rank} | **{team_name}** | {stats['games']} | {stats['wins']} | "
            f"{stats['draws']} | {stats['losses']} | {stats['goals_for']} | "
            f"{stats['goals_against']} | {gd_str} | **{stats['points']}** | "
            f"{stats['win_rate']:.0f}% |"
        )

    return lines


def _export_schedule(tournament: Tournament) -> list[str]:
    """Export schedule table as Markdown."""
    lines = []

    round_count = tournament.current_round_count
    has_multiple_rounds = round_count > 1

    # Determine if we need sitting out column
    all_players = [p.name for p in tournament.players]
    players_per_match = tournament.team1_size + tournament.team2_size
    show_sitting_out = len(all_players) > players_per_match

    # Separate played and pending matches
    played_matches = [m for m in tournament.matches if m.played]
    pending_matches = [m for m in tournament.matches if not m.played]

    if played_matches:
        lines.append("### Completed Matches")
        lines.append("")

        if has_multiple_rounds:
            # Group by round
            rounds = sorted(set(m.round for m in played_matches))
            for round_num in rounds:
                round_matches = [m for m in played_matches if m.round == round_num]
                lines.append(f"#### Round {round_num}")
                lines.append("")
                lines.extend(_export_match_table(round_matches, played=True, all_players=all_players if show_sitting_out else None))
                lines.append("")
        else:
            lines.extend(_export_match_table(played_matches, played=True, all_players=all_players if show_sitting_out else None))
            lines.append("")

    if pending_matches:
        lines.append("### Upcoming Matches")
        lines.append("")

        if has_multiple_rounds:
            # Group by round
            rounds = sorted(set(m.round for m in pending_matches))
            for round_num in rounds:
                round_matches = [m for m in pending_matches if m.round == round_num]
                lines.append(f"#### Round {round_num}")
                lines.append("")
                lines.extend(_export_match_table(round_matches, played=False, all_players=all_players if show_sitting_out else None))
                lines.append("")
        else:
            lines.extend(_export_match_table(pending_matches, played=False, all_players=all_players if show_sitting_out else None))
            lines.append("")

    # Summary
    summary = f"**Played:** {tournament.played_matches} | **Remaining:** {tournament.remaining_matches} | **Total:** {tournament.total_matches}"
    if has_multiple_rounds:
        summary += f" | **Rounds:** {round_count}"
    lines.append(summary)

    return lines


def _export_match_table(matches: list, played: bool, all_players: Optional[list[str]] = None) -> list[str]:
    """Export a table of matches.

    Args:
        matches: List of Match objects
        played: Whether these are played matches (affects columns shown)
        all_players: If provided, adds a "Sitting Out" column showing who's not playing
    """
    lines = []
    show_sitting_out = all_players is not None

    if played:
        if show_sitting_out:
            lines.append("| # | Team 1 | Score | Team 2 | Sitting Out |")
            lines.append("|:-:|--------|:-----:|--------|-------------|")
        else:
            lines.append("| # | Team 1 | Score | Team 2 |")
            lines.append("|:-:|--------|:-----:|--------|")

        for match in matches:
            team1_name = format_team(match.team1)
            team2_name = format_team(match.team2)

            # Bold the winning team
            if match.is_draw:
                team1_str = team1_name
                team2_str = team2_name
            elif match.score1 > match.score2:
                team1_str = f"**{team1_name}**"
                team2_str = team2_name
            else:
                team1_str = team1_name
                team2_str = f"**{team2_name}**"

            score_str = f"{match.score1} - {match.score2}"

            if show_sitting_out:
                sitting = get_sitting_out(match, all_players)
                sitting_str = ", ".join(sitting) if sitting else "-"
                lines.append(f"| {match.id} | {team1_str} | {score_str} | {team2_str} | {sitting_str} |")
            else:
                lines.append(f"| {match.id} | {team1_str} | {score_str} | {team2_str} |")
    else:
        if show_sitting_out:
            lines.append("| # | Team 1 | vs | Team 2 | Sitting Out |")
            lines.append("|:-:|--------|:--:|--------|-------------|")
        else:
            lines.append("| # | Team 1 | vs | Team 2 |")
            lines.append("|:-:|--------|:--:|--------|")

        for match in matches:
            team1_str = format_team(match.team1)
            team2_str = format_team(match.team2)

            if show_sitting_out:
                sitting = get_sitting_out(match, all_players)
                sitting_str = ", ".join(sitting) if sitting else "-"
                lines.append(f"| {match.id} | {team1_str} | vs | {team2_str} | {sitting_str} |")
            else:
                lines.append(f"| {match.id} | {team1_str} | vs | {team2_str} |")

    return lines


def _export_player_stats(player: Player, tournament: Tournament) -> list[str]:
    """Export individual player stats as Markdown."""
    lines = []
    s = player.stats

    lines.append(f"### {player.name}")
    lines.append("")

    # Basic stats
    gd = s.goal_difference
    gd_str = f"+{gd}" if gd > 0 else str(gd)

    lines.append(f"- **Games Played:** {s.games_played}")
    lines.append(f"- **Record:** {s.wins}W / {s.draws}D / {s.losses}L")
    lines.append(f"- **Points:** {s.points}")
    lines.append(f"- **Win Rate:** {s.win_rate:.1f}%")
    lines.append(f"- **Goals:** {s.goals_scored} scored, {s.goals_conceded} conceded (GD: {gd_str})")

    # Partnership stats
    partnership_stats = calculate_partnership_stats(player.name, tournament)
    if partnership_stats:
        lines.append("")
        lines.append("**Partnerships:**")
        lines.append("")
        lines.append("| Partner | P | W | D | L | Win% |")
        lines.append("|---------|:-:|:-:|:-:|:-:|:----:|")

        for partner, stats in sorted(partnership_stats.items(), key=lambda x: x[1]["wins"], reverse=True):
            total = stats["wins"] + stats["draws"] + stats["losses"]
            win_rate = (stats["wins"] / total * 100) if total > 0 else 0
            lines.append(
                f"| {partner} | {total} | {stats['wins']} | {stats['draws']} | "
                f"{stats['losses']} | {win_rate:.0f}% |"
            )

    return lines


def save_markdown_export(tournament: Tournament, path: Optional[Path] = None) -> Path:
    """Save tournament export to a Markdown file."""
    if path is None:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in tournament.name)
        path = Path(f"{safe_name}_export.md")

    content = export_tournament_markdown(tournament)
    path.write_text(content)
    return path


def export_tournament_pdf(tournament: Tournament, path: Optional[Path] = None) -> Path:
    """Export tournament to a styled PDF file."""
    import markdown
    from weasyprint import HTML, CSS

    if path is None:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in tournament.name)
        path = Path(f"{safe_name}_export.pdf")

    # Convert markdown to HTML
    md_content = export_tournament_markdown(tournament)
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )

    # Wrap in full HTML document
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{tournament.name} - Tournament Summary</title>
</head>
<body>
{html_body}
</body>
</html>"""

    # Generate PDF with styling
    html_doc = HTML(string=html_content)
    css = CSS(string=PDF_CSS)
    html_doc.write_pdf(path, stylesheets=[css])

    return path
