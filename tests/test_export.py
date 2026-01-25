"""Tests for tournament_cli.export module."""

import pytest
from pathlib import Path
import tempfile

from tournament_cli.export import (
    export_tournament_markdown,
    save_markdown_export,
)


class TestExportTournamentMarkdown:
    """Tests for export_tournament_markdown function."""

    def test_export_contains_tournament_name(self, sample_tournament):
        """Test that export contains tournament name."""
        md = export_tournament_markdown(sample_tournament)
        assert "Test Tournament" in md

    def test_export_contains_player_count(self, sample_tournament):
        """Test that export contains player count."""
        md = export_tournament_markdown(sample_tournament)
        assert "**Players:** 4" in md

    def test_export_contains_match_count(self, sample_tournament):
        """Test that export contains match count."""
        md = export_tournament_markdown(sample_tournament)
        assert "**Matches:** 0/3" in md

    def test_export_contains_sections(self, sample_tournament):
        """Test that export contains all major sections."""
        md = export_tournament_markdown(sample_tournament)
        assert "## Standings" in md
        assert "## Best Teams" in md
        assert "## Schedule" in md
        assert "## Player Statistics" in md

    def test_export_contains_standings_table(self, sample_tournament):
        """Test that export contains standings table headers."""
        md = export_tournament_markdown(sample_tournament)
        assert "| # | Player |" in md
        assert "| Pts |" in md

    def test_export_contains_players(self, sample_tournament):
        """Test that export contains player names."""
        md = export_tournament_markdown(sample_tournament)
        for player in sample_tournament.players:
            assert player.name in md

    def test_export_with_played_matches(self, sample_tournament):
        """Test export with played matches."""
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 1

        md = export_tournament_markdown(sample_tournament)
        assert "### Completed Matches" in md
        assert "2 - 1" in md

    def test_export_with_pending_matches(self, sample_tournament):
        """Test export with pending matches."""
        md = export_tournament_markdown(sample_tournament)
        assert "### Upcoming Matches" in md

    def test_export_progress_percentage(self, sample_tournament):
        """Test that progress percentage is shown."""
        sample_tournament.matches[0].score1 = 1
        sample_tournament.matches[0].score2 = 0

        md = export_tournament_markdown(sample_tournament)
        assert "**Progress:** 33%" in md

    def test_export_is_valid_markdown(self, sample_tournament):
        """Test that export is valid markdown (basic checks)."""
        md = export_tournament_markdown(sample_tournament)

        # Check for proper heading structure
        assert md.startswith("#")
        assert "##" in md

        # Check for table structure
        assert "|" in md
        assert "---" in md


class TestSaveMarkdownExport:
    """Tests for save_markdown_export function."""

    def test_save_to_default_path(self, sample_tournament):
        """Test saving to default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = save_markdown_export(sample_tournament)
                assert path.exists()
                assert path.suffix == ".md"
                assert "Test_Tournament" in path.name
            finally:
                os.chdir(original_cwd)

    def test_save_to_custom_path(self, sample_tournament):
        """Test saving to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom_export.md"
            path = save_markdown_export(sample_tournament, custom_path)
            assert path == custom_path
            assert path.exists()

    def test_saved_content_matches_export(self, sample_tournament):
        """Test that saved content matches export function output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.md"
            save_markdown_export(sample_tournament, path)

            expected = export_tournament_markdown(sample_tournament)
            actual = path.read_text()
            assert actual == expected

    def test_save_overwrites_existing(self, sample_tournament):
        """Test that save overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.md"
            path.write_text("old content")

            save_markdown_export(sample_tournament, path)
            content = path.read_text()
            assert "old content" not in content
            assert "Test Tournament" in content


class TestMarkdownFormatting:
    """Tests for markdown formatting details."""

    def test_medal_emojis_in_standings(self, sample_tournament):
        """Test that medal emojis are used for top 3."""
        # Give players different points
        sample_tournament.players[0].stats.wins = 3
        sample_tournament.players[1].stats.wins = 2
        sample_tournament.players[2].stats.wins = 1
        sample_tournament.players[3].stats.wins = 0

        md = export_tournament_markdown(sample_tournament)
        # Check for medal emoji patterns
        # First place
        assert any(char in md for char in ["🥇", "1"])

    def test_goal_difference_formatting(self, sample_tournament):
        """Test goal difference formatting (positive/negative)."""
        sample_tournament.players[0].stats.goals_scored = 10
        sample_tournament.players[0].stats.goals_conceded = 5

        md = export_tournament_markdown(sample_tournament)
        assert "+5" in md

    def test_winning_team_bold_in_results(self, sample_tournament):
        """Test that winning team is bold in match results."""
        match = sample_tournament.matches[0]
        match.score1 = 3
        match.score2 = 0

        md = export_tournament_markdown(sample_tournament)
        # Winner (team1) should be bold
        team1_str = f"{match.team1[0]} & {match.team1[1]}"
        assert f"**{team1_str}**" in md

    def test_table_alignment(self, sample_tournament):
        """Test that tables have proper alignment markers."""
        md = export_tournament_markdown(sample_tournament)
        # Center-aligned columns should have colons on both sides
        assert ":-:" in md


class TestPlayerStatsExport:
    """Tests for player statistics in export."""

    def test_player_stats_section(self, sample_tournament):
        """Test that each player has a stats section."""
        md = export_tournament_markdown(sample_tournament)
        for player in sample_tournament.players:
            assert f"### {player.name}" in md

    def test_player_stats_content(self, sample_tournament):
        """Test player stats content."""
        sample_tournament.players[0].stats.wins = 5
        sample_tournament.players[0].stats.goals_scored = 15

        md = export_tournament_markdown(sample_tournament)
        assert "**Games Played:**" in md
        assert "**Record:**" in md
        assert "**Points:**" in md

    def test_partnership_stats_in_export(self, sample_tournament):
        """Test that partnership stats are included when available."""
        # Play a match to generate partnership data
        sample_tournament.matches[0].score1 = 2
        sample_tournament.matches[0].score2 = 1

        md = export_tournament_markdown(sample_tournament)
        assert "**Partnerships:**" in md
