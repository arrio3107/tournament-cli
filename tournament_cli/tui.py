"""Interactive TUI mode for tournament management using Textual."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, DataTable, Input, Footer
from textual.screen import ModalScreen
from textual import on
from typing import Optional

from tournament_cli.storage import get_current_tournament, save_current_tournament, set_current_tournament
from tournament_cli.display import format_team, calculate_team_stats, calculate_partnership_stats
from tournament_cli.matchmaking import get_sitting_out
from tournament_cli.models import Tournament, Match


class NoTournamentScreen(ModalScreen):
    """Screen shown when no tournament is loaded."""

    def compose(self) -> ComposeResult:
        yield Static(
            "\n  No tournament loaded.\n\n"
            "  Use the CLI to create or load a tournament first:\n\n"
            "    tournament-cli new <name>\n"
            "    tournament-cli load <name>\n\n"
            "  Press Q to quit.\n",
            id="no-tournament-message",
        )

    def key_q(self) -> None:
        self.app.exit()


class PlayerStatsModal(ModalScreen):
    """Modal screen displaying detailed player statistics."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close", show=True),
        Binding("q", "dismiss_modal", "Close", show=False),
    ]

    def __init__(self, player_name: str, tournament: Tournament) -> None:
        super().__init__()
        self.player_name = player_name
        self.tournament = tournament

    def compose(self) -> ComposeResult:
        player = self.tournament.get_player(self.player_name)
        if not player:
            yield Static("Player not found", id="stats-content")
            return

        s = player.stats
        games = s.wins + s.draws + s.losses
        win_rate = (s.wins / games * 100) if games > 0 else 0
        gd = s.goal_difference
        gd_str = f"+{gd}" if gd > 0 else str(gd)

        lines = [
            f"[bold #89b4fa]{self.player_name}[/]",
            "",
            f"[#6c7086]Games Played:[/]  [#cdd6f4]{games}[/]",
            f"[#6c7086]Record:[/]        [#a6e3a1]{s.wins}W[/] / [#f9e2af]{s.draws}D[/] / [#f38ba8]{s.losses}L[/]",
            f"[#6c7086]Points:[/]        [bold #cdd6f4]{s.points}[/]",
            f"[#6c7086]Win Rate:[/]      [#cdd6f4]{win_rate:.1f}%[/]",
            "",
            f"[#6c7086]Goals Scored:[/]  [#cdd6f4]{s.goals_scored}[/]",
            f"[#6c7086]Goals Conceded:[/] [#cdd6f4]{s.goals_conceded}[/]",
            f"[#6c7086]Goal Diff:[/]     [#cdd6f4]{gd_str}[/]",
        ]

        # Add partnership stats if in team mode
        if self.tournament.mode != "1v1":
            partnership_stats = calculate_partnership_stats(self.player_name, self.tournament)
            if partnership_stats:
                lines.append("")
                lines.append("[bold #89b4fa]Partnerships[/]")
                lines.append("[#6c7086]Partner          W   D   L[/]")

                # Sort by wins then by losses (ascending)
                sorted_partners = sorted(
                    partnership_stats.items(),
                    key=lambda x: (x[1]["wins"], -x[1]["losses"]),
                    reverse=True
                )

                for partner, pstats in sorted_partners:
                    lines.append(
                        f"[#cdd6f4]{partner:<16}[/] "
                        f"[#a6e3a1]{pstats['wins']:<3}[/] "
                        f"[#f9e2af]{pstats['draws']:<3}[/] "
                        f"[#f38ba8]{pstats['losses']:<3}[/]"
                    )

        lines.append("")
        lines.append("[#6c7086]Press [#89b4fa]q[/] or [#89b4fa]Esc[/] to close[/]")

        yield Static("\n".join(lines), id="stats-content")

    def action_dismiss_modal(self) -> None:
        self.dismiss()


class ScoreInput(Static):
    """Widget for entering match scores."""

    can_focus = False  # Only the Input widgets inside should be focusable

    def __init__(self) -> None:
        super().__init__()
        self.match: Optional[Match] = None
        self.score1_input: Optional[Input] = None
        self.score2_input: Optional[Input] = None
        self.border_title = "Score Entry (i)"

    def compose(self) -> ComposeResult:
        with Horizontal(id="score-row"):
            yield Static("", id="team1-label")
            yield Input(placeholder="0", id="score1", type="integer")
            yield Static(" vs ", id="vs-label")
            yield Input(placeholder="0", id="score2", type="integer")
            yield Static("", id="team2-label")

    def on_mount(self) -> None:
        self.score1_input = self.query_one("#score1", Input)
        self.score2_input = self.query_one("#score2", Input)

    def set_match(self, match: Optional[Match]) -> None:
        """Update the displayed match."""
        self.match = match
        team1_label = self.query_one("#team1-label", Static)
        team2_label = self.query_one("#team2-label", Static)

        if match is None:
            self.border_title = "All matches complete!"
            team1_label.update("")
            team2_label.update("")
            self.score1_input.value = ""
            self.score2_input.value = ""
            self.score1_input.disabled = True
            self.score2_input.disabled = True
        else:
            status = "✓" if match.played else ""
            self.border_title = f"Match #{match.id} {status}"
            team1_label.update(format_team(match.team1))
            team2_label.update(format_team(match.team2))
            self.score1_input.disabled = False
            self.score2_input.disabled = False

            if match.played:
                self.score1_input.value = str(match.score1)
                self.score2_input.value = str(match.score2)
            else:
                self.score1_input.value = ""
                self.score2_input.value = ""

    def get_scores(self) -> tuple[Optional[int], Optional[int]]:
        """Get the current score values."""
        try:
            score1 = int(self.score1_input.value) if self.score1_input.value else None
        except ValueError:
            score1 = None
        try:
            score2 = int(self.score2_input.value) if self.score2_input.value else None
        except ValueError:
            score2 = None
        return score1, score2

    def focus_score1(self) -> None:
        """Focus the first score input."""
        if self.score1_input and not self.score1_input.disabled:
            self.score1_input.focus()


class MatchList(Static):
    """Widget displaying the list of matches."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self.tournament: Optional[Tournament] = None
        self.selected_index: int = 0
        self.border_title = "Matches (m)"

    def compose(self) -> ComposeResult:
        yield Static("", id="matches-content")

    def set_tournament(self, tournament: Optional[Tournament]) -> None:
        """Update the tournament data."""
        self.tournament = tournament
        if tournament and tournament.matches:
            # Select first unplayed match by default
            for i, m in enumerate(tournament.matches):
                if not m.played:
                    self.selected_index = i
                    break
            # Update title with progress
            played = sum(1 for m in tournament.matches if m.played)
            total = len(tournament.matches)
            self.border_title = f"Matches ({played}/{total}) (m)"
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the match list display."""
        content = self.query_one("#matches-content", Static)

        if not self.tournament or not self.tournament.matches:
            content.update("No matches")
            return

        # Update title with progress
        played = sum(1 for m in self.tournament.matches if m.played)
        total = len(self.tournament.matches)
        self.border_title = f"Matches ({played}/{total}) (m)"

        # Get all player names for sitting out calculation
        all_players = [p.name for p in self.tournament.players]
        players_per_match = self.tournament.team1_size + self.tournament.team2_size
        show_sitting_out = len(all_players) > players_per_match

        lines = []
        for i, match in enumerate(self.tournament.matches):
            team1 = format_team(match.team1)
            team2 = format_team(match.team2)

            # Status indicator and score
            if match.played:
                status = "[#a6e3a1]✓[/]"
                score = f"[#89b4fa]{match.score1}-{match.score2}[/]"
            else:
                status = " "
                score = "[#45475a]–[/]"

            # Build the line content
            match_text = f"{status} #{match.id:2d}  {team1} vs {team2}  {score}"

            # Add sitting out info if applicable
            if show_sitting_out:
                sitting = get_sitting_out(match, all_players)
                if sitting:
                    sitting_text = f"[#6c7086]  ⌛ {', '.join(sitting)}[/]"
                    match_text += sitting_text

            # Selected row gets background highlight
            if i == self.selected_index:
                line = f"[on #313244][bold #cdd6f4]{match_text}[/][/]"
            else:
                line = f"[#bac2de]{match_text}[/]"

            lines.append(line)

        content.update("\n".join(lines))

    def select_next(self) -> Optional[Match]:
        """Select the next match."""
        if self.tournament and self.tournament.matches:
            self.selected_index = min(self.selected_index + 1, len(self.tournament.matches) - 1)
            self.refresh_display()
            self._scroll_to_selected()
            return self.tournament.matches[self.selected_index]
        return None

    def select_prev(self) -> Optional[Match]:
        """Select the previous match."""
        if self.tournament and self.tournament.matches:
            self.selected_index = max(self.selected_index - 1, 0)
            self.refresh_display()
            self._scroll_to_selected()
            return self.tournament.matches[self.selected_index]
        return None

    def _scroll_to_selected(self) -> None:
        """Scroll to keep the selected match visible."""
        # Each match is one line, scroll to that line
        self.scroll_to(y=self.selected_index, animate=False)

    def get_selected_match(self) -> Optional[Match]:
        """Get the currently selected match."""
        if self.tournament and self.tournament.matches:
            return self.tournament.matches[self.selected_index]
        return None


class StandingsTable(Static):
    """Widget displaying player standings."""

    can_focus = False  # DataTable inside handles focus

    def __init__(self) -> None:
        super().__init__()
        self.tournament: Optional[Tournament] = None
        self.border_title = "Standings (s)"
        self._player_order: list = []  # Track player names by row

    def compose(self) -> ComposeResult:
        yield DataTable(id="standings-table")

    def on_mount(self) -> None:
        table = self.query_one("#standings-table", DataTable)
        table.add_columns("#", "Player", "W", "D", "L", "GD", "Pts")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def set_tournament(self, tournament: Optional[Tournament]) -> None:
        """Update the tournament data."""
        self.tournament = tournament
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the standings display."""
        table = self.query_one("#standings-table", DataTable)
        table.clear()
        self._player_order = []

        if not self.tournament:
            return

        # Sort players by points, then goal difference, then goals scored
        sorted_players = sorted(
            self.tournament.players,
            key=lambda p: (p.stats.points, p.stats.goal_difference, p.stats.goals_scored),
            reverse=True
        )

        for i, player in enumerate(sorted_players, 1):
            s = player.stats
            gd = s.goal_difference
            gd_str = f"+{gd}" if gd > 0 else str(gd)
            self._player_order.append(player.name)

            table.add_row(
                str(i),
                player.name,
                str(s.wins),
                str(s.draws),
                str(s.losses),
                gd_str,
                str(s.points),
            )

    def get_selected_player_name(self) -> Optional[str]:
        """Get the name of the currently selected player."""
        table = self.query_one("#standings-table", DataTable)
        row_index = table.cursor_row
        if 0 <= row_index < len(self._player_order):
            return self._player_order[row_index]
        return None


class TeamStatsTable(Static):
    """Widget displaying team statistics."""

    can_focus = False  # Display only, not interactive

    def __init__(self) -> None:
        super().__init__()
        self.tournament: Optional[Tournament] = None
        self.border_title = "Teams"

    def compose(self) -> ComposeResult:
        yield DataTable(id="teams-table")

    def on_mount(self) -> None:
        table = self.query_one("#teams-table", DataTable)
        table.add_columns("#", "Team", "W", "D", "L", "GD", "Pts")
        table.cursor_type = "none"
        table.zebra_stripes = True
        table.can_focus = False  # Display only, not interactive

    def set_tournament(self, tournament: Optional[Tournament]) -> None:
        """Update the tournament data."""
        self.tournament = tournament
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the team stats display."""
        table = self.query_one("#teams-table", DataTable)
        table.clear()

        if not self.tournament:
            return

        team_stats = calculate_team_stats(self.tournament)

        for i, stats in enumerate(team_stats, 1):
            team_name = format_team(stats['players'])
            gd = stats["goal_diff"]
            gd_str = f"+{gd}" if gd > 0 else str(gd)

            table.add_row(
                str(i),
                team_name,
                str(stats["wins"]),
                str(stats["draws"]),
                str(stats["losses"]),
                gd_str,
                str(stats["points"]),
            )


class TournamentApp(App):
    """Main TUI application for tournament management."""

    CSS = """
    /* Lazygit-inspired theme using Catppuccin Mocha colors */
    $primary: #89b4fa;           /* Blue for active elements */
    $primary-muted: #45475a;     /* Gray for inactive borders */
    $success: #a6e3a1;           /* Green for completed */
    $text: #cdd6f4;              /* Light text */
    $text-muted: #6c7086;        /* Muted text */
    $surface: #1e1e2e;           /* Dark background */
    $selection: #313244;         /* Selected row background */

    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr auto;
        background: $surface;
    }

    #no-tournament-message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        background: $surface;
        color: $text;
    }

    /* Panel styling - lazygit uses rounded borders */
    MatchList {
        height: 100%;
        border: round $primary-muted;
        border-title-align: left;
        border-title-color: $text-muted;
        border-title-style: bold;
        padding: 0 1;
        background: $surface;
        overflow-y: auto;
    }

    MatchList:focus {
        border: round $primary;
        border-title-color: $primary;
    }

    #matches-content {
        height: auto;
        background: $surface;
    }

    /* Right column container for standings + team stats */
    #right-column {
        height: 100%;
        background: $surface;
    }

    StandingsTable {
        height: 1fr;
        border: round $primary-muted;
        border-title-align: left;
        border-title-color: $text-muted;
        border-title-style: bold;
        padding: 0 1;
        background: $surface;
    }

    StandingsTable:focus-within {
        border: round $primary;
        border-title-color: $primary;
    }

    #standings-table {
        height: auto;
        background: $surface;
    }

    #standings-table > .datatable--header {
        color: $text-muted;
        text-style: bold;
        background: $surface;
    }

    #standings-table > .datatable--odd-row {
        background: $surface;
    }

    #standings-table > .datatable--even-row {
        background: $selection;
    }

    TeamStatsTable {
        height: 1fr;
        border: round $primary-muted;
        border-title-align: left;
        border-title-color: $text-muted;
        border-title-style: bold;
        padding: 0 1;
        background: $surface;
    }


    #teams-table {
        height: auto;
        background: $surface;
    }

    #teams-table > .datatable--header {
        color: $text-muted;
        text-style: bold;
        background: $surface;
    }

    #teams-table > .datatable--odd-row {
        background: $surface;
    }

    #teams-table > .datatable--even-row {
        background: $selection;
    }

    ScoreInput {
        column-span: 2;
        height: auto;
        min-height: 7;
        border: round $primary-muted;
        border-title-align: left;
        border-title-color: $text-muted;
        border-title-style: bold;
        padding: 1 2;
        background: $surface;
    }

    ScoreInput:focus-within {
        border: round $primary;
        border-title-color: $primary;
    }

    #score-row {
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #team1-label {
        width: auto;
        min-width: 24;
        text-align: right;
        padding-right: 2;
        color: $text;
        text-style: bold;
    }

    #team2-label {
        width: auto;
        min-width: 24;
        text-align: left;
        padding-left: 2;
        color: $text;
        text-style: bold;
    }

    #vs-label {
        width: auto;
        padding: 0 1;
        color: $text-muted;
        text-style: bold;
    }

    Input {
        width: 11;
        height: 3;
        background: $selection;
        border: tall $primary-muted;
        content-align: center middle;
        text-align: center;
        text-style: bold;
    }

    Input > .input--cursor {
        color: $text;
        background: $primary;
    }

    Input:focus {
        border: tall $primary;
    }

    Input.-valid {
        border: tall $primary-muted;
    }

    Input.-valid:focus {
        border: tall $primary;
    }

    /* Minimal footer like lazygit keybinding hints */
    Footer {
        column-span: 2;
        background: $surface;
        color: $text-muted;
    }

    Footer > .footer--key {
        color: $primary;
        background: transparent;
    }

    Footer > .footer--description {
        color: $text-muted;
    }

    /* Modal styling */
    PlayerStatsModal {
        align: center middle;
    }

    #stats-content {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 2 3;
        background: $surface;
        border: round $primary;
    }

    /* DataTable cursor styling */
    #standings-table > .datatable--cursor {
        background: $primary;
        color: $surface;
    }

    """

    BINDINGS = [
        Binding("q", "quit", "quit"),
        Binding("up,k", "prev_match", "up", show=False),
        Binding("down,j", "next_match", "down", show=False),
        Binding("j", "next_match", "↓", show=True),
        Binding("k", "prev_match", "↑", show=True),
        Binding("enter", "save_score", "save"),
        Binding("n", "next_unplayed", "next"),
        Binding("r", "refresh", "refresh"),
        Binding("m", "focus_matches", "matches", show=True),
        Binding("s", "focus_standings", "standings", show=True),
        Binding("i", "focus_scores", "input", show=True),
        Binding("tab", "focus_next_panel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.tournament: Optional[Tournament] = None

    def compose(self) -> ComposeResult:
        yield MatchList()
        with Vertical(id="right-column"):
            yield StandingsTable()
            yield TeamStatsTable()
        yield ScoreInput()
        yield Footer()

    def on_mount(self) -> None:
        """Load tournament on startup."""
        self.tournament = get_current_tournament()

        if not self.tournament:
            self.push_screen(NoTournamentScreen())
            return

        # Show/hide team stats based on mode
        self._update_team_stats_visibility()

        self.refresh_all()

        # Focus the score input
        score_input = self.query_one(ScoreInput)
        score_input.focus_score1()

    def _update_team_stats_visibility(self) -> None:
        """Show or hide team stats based on tournament mode."""
        team_stats = self.query_one(TeamStatsTable)
        standings = self.query_one(StandingsTable)

        if self.tournament and self.tournament.mode != "1v1":
            team_stats.display = True
            # Both take equal space
        else:
            team_stats.display = False
            # Standings takes full height

    def refresh_all(self) -> None:
        """Refresh all widgets with current tournament data."""
        match_list = self.query_one(MatchList)
        standings = self.query_one(StandingsTable)
        score_input = self.query_one(ScoreInput)

        match_list.set_tournament(self.tournament)
        standings.set_tournament(self.tournament)
        score_input.set_match(match_list.get_selected_match())

        # Refresh team stats if visible
        if self.tournament and self.tournament.mode != "1v1":
            team_stats = self.query_one(TeamStatsTable)
            team_stats.set_tournament(self.tournament)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_prev_match(self) -> None:
        """Navigate up in the focused panel."""
        # Check if standings DataTable has focus
        standings_table = self.query_one("#standings-table", DataTable)
        if standings_table.has_focus:
            standings_table.action_cursor_up()
            return

        # Default: navigate matches
        match_list = self.query_one(MatchList)
        match = match_list.select_prev()
        if match:
            score_input = self.query_one(ScoreInput)
            score_input.set_match(match)

    def action_next_match(self) -> None:
        """Navigate down in the focused panel."""
        # Check if standings DataTable has focus
        standings_table = self.query_one("#standings-table", DataTable)
        if standings_table.has_focus:
            standings_table.action_cursor_down()
            return

        # Default: navigate matches
        match_list = self.query_one(MatchList)
        match = match_list.select_next()
        if match:
            score_input = self.query_one(ScoreInput)
            score_input.set_match(match)

    def action_next_unplayed(self) -> None:
        """Jump to next unplayed match."""
        if not self.tournament:
            return

        match_list = self.query_one(MatchList)
        for i, m in enumerate(self.tournament.matches):
            if not m.played:
                match_list.selected_index = i
                match_list.refresh_display()
                score_input = self.query_one(ScoreInput)
                score_input.set_match(m)
                score_input.focus_score1()
                break

    def action_save_score(self) -> None:
        """Save the current match score, or jump to input if matches focused."""
        if not self.tournament:
            return

        # If matches list is focused, jump to score input instead of saving
        match_list = self.query_one(MatchList)
        if match_list.has_focus:
            self.query_one(ScoreInput).focus_score1()
            return

        score_input = self.query_one(ScoreInput)
        match = score_input.match

        if not match:
            return

        score1, score2 = score_input.get_scores()

        if score1 is None or score2 is None:
            self.notify("Please enter both scores", severity="warning")
            return

        if score1 < 0 or score2 < 0:
            self.notify("Scores cannot be negative", severity="error")
            return

        # If match was already played, reverse previous stats
        if match.played:
            self._reverse_match_stats(match)

        # Update match
        match.score1 = score1
        match.score2 = score2

        # Update player stats
        self._update_player_stats(match)

        # Save tournament
        save_current_tournament()

        # Refresh display
        self.refresh_all()

        # Show result
        if match.is_draw:
            self.notify(f"Draw! {score1} - {score2}", severity="information")
        else:
            winner = format_team(match.winner)
            self.notify(f"{winner} wins {max(score1, score2)} - {min(score1, score2)}!", severity="information")

        # Move to next unplayed match
        self.action_next_unplayed()

    def action_refresh(self) -> None:
        """Reload tournament from disk."""
        # Clear the cache by resetting and reloading
        set_current_tournament(None)
        self.tournament = get_current_tournament()
        if self.tournament:
            self._update_team_stats_visibility()
            self.refresh_all()
            self.notify("Refreshed", severity="information")

    def action_focus_matches(self) -> None:
        """Focus the matches panel."""
        self.query_one(MatchList).focus()

    def action_focus_standings(self) -> None:
        """Focus the standings table."""
        table = self.query_one("#standings-table", DataTable)
        table.focus()

    def action_focus_scores(self) -> None:
        """Focus the score input."""
        self.query_one(ScoreInput).focus_score1()

    def action_focus_next_panel(self) -> None:
        """Cycle focus to the next panel: matches -> standings -> input."""
        match_list = self.query_one(MatchList)
        standings_table = self.query_one("#standings-table", DataTable)

        if match_list.has_focus:
            standings_table.focus()
        elif standings_table.has_focus:
            self.query_one(ScoreInput).focus_score1()
        else:
            match_list.focus()

    @on(DataTable.RowSelected, "#standings-table")
    def on_standings_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter key on standings table row."""
        standings = self.query_one(StandingsTable)
        player_name = standings.get_selected_player_name()
        if player_name and self.tournament:
            self.push_screen(PlayerStatsModal(player_name, self.tournament))

    def _update_player_stats(self, match: Match) -> None:
        """Update player statistics after a match."""
        if not self.tournament:
            return

        team1_players = [self.tournament.get_player(name) for name in match.team1]
        team2_players = [self.tournament.get_player(name) for name in match.team2]

        if match.is_draw:
            for player in team1_players + team2_players:
                if player:
                    player.stats.draws += 1
                    if player in team1_players:
                        player.stats.goals_scored += match.score1
                        player.stats.goals_conceded += match.score2
                    else:
                        player.stats.goals_scored += match.score2
                        player.stats.goals_conceded += match.score1
        else:
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

    def _reverse_match_stats(self, match: Match) -> None:
        """Reverse player statistics for a match (when re-recording)."""
        if not self.tournament or not match.played:
            return

        team1_players = [self.tournament.get_player(name) for name in match.team1]
        team2_players = [self.tournament.get_player(name) for name in match.team2]

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

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        if event.input.id == "score1":
            # Move to score2
            score2_input = self.query_one("#score2", Input)
            score2_input.focus()
        elif event.input.id == "score2":
            # Save the score
            self.action_save_score()


def main() -> None:
    """Entry point for the TUI."""
    app = TournamentApp()
    app.run()


if __name__ == "__main__":
    main()
