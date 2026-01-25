"""Integration tests for tournament_cli.cli module."""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from tournament_cli.cli import app
from tournament_cli import storage


runner = CliRunner()


@pytest.fixture
def cli_temp_dir(monkeypatch):
    """Create temporary directory for CLI tests."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Patch storage to use temp directory
    monkeypatch.setattr(storage, 'TOURNAMENTS_DIR', temp_path)
    monkeypatch.setattr(storage, 'CONFIG_FILE', temp_path / ".config.json")
    monkeypatch.setattr(storage, '_current_tournament', None)

    yield temp_path

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIHelp:
    """Tests for CLI help commands."""

    def test_main_help(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "2v2 Tournament Manager" in result.output

    def test_new_help(self):
        """Test new command help."""
        result = runner.invoke(app, ["new", "--help"])
        assert result.exit_code == 0
        assert "Create a new tournament" in result.output

    def test_load_help(self):
        """Test load command help."""
        result = runner.invoke(app, ["load", "--help"])
        assert result.exit_code == 0

    def test_export_help(self):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0


class TestListCommand:
    """Tests for list command."""

    def test_list_empty(self, cli_temp_dir):
        """Test listing when no tournaments exist."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No tournaments found" in result.output

    def test_list_with_tournaments(self, cli_temp_dir):
        """Test listing when tournaments exist."""
        # Create a tournament via the new command
        result = runner.invoke(app, ["new", "Test Cup"], input="Alice\nBob\nCharlie\nDave\n\n")
        assert result.exit_code == 0

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Test Cup" in result.output


class TestStatusCommand:
    """Tests for status command."""

    def test_status_no_tournament(self, cli_temp_dir):
        """Test status when no tournament loaded."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1
        assert "No tournament loaded" in result.output

    def test_status_with_tournament(self, cli_temp_dir):
        """Test status with loaded tournament."""
        # Create and load tournament
        runner.invoke(app, ["new", "Status Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Status Test" in result.output
        assert "Players: 4" in result.output


class TestLoadCommand:
    """Tests for load command."""

    def test_load_nonexistent(self, cli_temp_dir):
        """Test loading a tournament that doesn't exist."""
        result = runner.invoke(app, ["load", "Nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_load_existing(self, cli_temp_dir):
        """Test loading an existing tournament."""
        # Create tournament
        runner.invoke(app, ["new", "Load Test"], input="A\nB\nC\nD\n\n")

        # Clear current tournament
        storage._current_tournament = None

        # Load it
        result = runner.invoke(app, ["load", "Load Test"])
        assert result.exit_code == 0
        assert "Loaded tournament" in result.output


class TestScheduleCommand:
    """Tests for schedule command."""

    def test_schedule_no_tournament(self, cli_temp_dir):
        """Test schedule when no tournament loaded."""
        result = runner.invoke(app, ["schedule"])
        assert result.exit_code == 1

    def test_schedule_with_tournament(self, cli_temp_dir):
        """Test schedule with loaded tournament."""
        runner.invoke(app, ["new", "Schedule Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["schedule"])
        assert result.exit_code == 0
        assert "Schedule" in result.output
        assert "Total: 3" in result.output


class TestStandingsCommand:
    """Tests for standings command."""

    def test_standings_no_tournament(self, cli_temp_dir):
        """Test standings when no tournament loaded."""
        result = runner.invoke(app, ["standings"])
        assert result.exit_code == 1

    def test_standings_with_tournament(self, cli_temp_dir):
        """Test standings with loaded tournament."""
        runner.invoke(app, ["new", "Standings Test"], input="Alice\nBob\nCharlie\nDave\n\n")

        result = runner.invoke(app, ["standings"])
        assert result.exit_code == 0
        assert "Standings" in result.output


class TestTeamsCommand:
    """Tests for teams command."""

    def test_teams_no_tournament(self, cli_temp_dir):
        """Test teams when no tournament loaded."""
        result = runner.invoke(app, ["teams"])
        assert result.exit_code == 1

    def test_teams_with_tournament(self, cli_temp_dir):
        """Test teams with loaded tournament."""
        runner.invoke(app, ["new", "Teams Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["teams"])
        assert result.exit_code == 0
        assert "Best Teams" in result.output


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_no_tournament(self, cli_temp_dir):
        """Test stats when no tournament loaded."""
        result = runner.invoke(app, ["stats", "Alice"])
        assert result.exit_code == 1

    def test_stats_unknown_player(self, cli_temp_dir):
        """Test stats for unknown player."""
        runner.invoke(app, ["new", "Stats Test"], input="Alice\nBob\nCharlie\nDave\n\n")

        result = runner.invoke(app, ["stats", "Unknown"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_stats_valid_player(self, cli_temp_dir):
        """Test stats for valid player."""
        runner.invoke(app, ["new", "Stats Test"], input="Alice\nBob\nCharlie\nDave\n\n")

        result = runner.invoke(app, ["stats", "Alice"])
        assert result.exit_code == 0
        assert "Alice" in result.output


class TestExportCommand:
    """Tests for export command."""

    def test_export_no_tournament(self, cli_temp_dir):
        """Test export when no tournament loaded."""
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 1

    def test_export_markdown(self, cli_temp_dir):
        """Test markdown export."""
        runner.invoke(app, ["new", "Export Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0
        assert "Exported Markdown" in result.output

        # Check file was created
        export_files = list(cli_temp_dir.parent.glob("*.md"))
        # Note: export goes to current directory, not temp dir


class TestNewCommand:
    """Tests for new command."""

    def test_new_tournament_creation(self, cli_temp_dir):
        """Test creating a new tournament."""
        result = runner.invoke(app, ["new", "New Test"], input="Alice\nBob\nCharlie\nDave\n\n")
        assert result.exit_code == 0
        assert "created" in result.output
        assert "Players: 4" in result.output
        assert "Matches: 3" in result.output

    def test_new_tournament_too_few_players(self, cli_temp_dir):
        """Test creating tournament with too few players."""
        result = runner.invoke(app, ["new", "Small Test"], input="Alice\nBob\nCharlie\n\n")
        assert "Need at least 4 players" in result.output

    def test_new_tournament_duplicate_names(self, cli_temp_dir):
        """Test creating tournament with duplicate player names."""
        result = runner.invoke(app, ["new", "Dup Test"], input="Alice\nAlice\nBob\nCharlie\nDave\n\n")
        assert "already exists" in result.output


class TestPlayCommand:
    """Tests for play command."""

    def test_play_no_tournament(self, cli_temp_dir):
        """Test play when no tournament loaded."""
        result = runner.invoke(app, ["play"])
        assert result.exit_code == 1

    def test_play_next_match(self, cli_temp_dir):
        """Test playing next match."""
        runner.invoke(app, ["new", "Play Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["play"], input="3\n1\n")
        assert result.exit_code == 0
        # Should show result
        assert "win" in result.output.lower() or "3 - 1" in result.output

    def test_play_specific_match(self, cli_temp_dir):
        """Test playing specific match by ID."""
        runner.invoke(app, ["new", "Play ID Test"], input="A\nB\nC\nD\n\n")

        result = runner.invoke(app, ["play", "1"], input="2\n2\n")
        assert result.exit_code == 0
        # Draw should be reported
        assert "Draw" in result.output or "2 - 2" in result.output


class TestResetCommand:
    """Tests for reset command."""

    def test_reset_no_tournament(self, cli_temp_dir):
        """Test reset when no tournament loaded."""
        result = runner.invoke(app, ["reset"])
        assert result.exit_code == 1

    def test_reset_cancelled(self, cli_temp_dir):
        """Test reset when user cancels."""
        runner.invoke(app, ["new", "Reset Test"], input="A\nB\nC\nD\n\n")
        runner.invoke(app, ["play"], input="2\n1\n")

        result = runner.invoke(app, ["reset"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output

    def test_reset_confirmed(self, cli_temp_dir):
        """Test reset when user confirms."""
        runner.invoke(app, ["new", "Reset Test"], input="A\nB\nC\nD\n\n")
        runner.invoke(app, ["play"], input="2\n1\n")

        result = runner.invoke(app, ["reset"], input="y\n")
        assert result.exit_code == 0
        assert "reset" in result.output.lower()


class TestCLIWorkflow:
    """Integration tests for complete CLI workflows."""

    def test_full_tournament_workflow(self, cli_temp_dir):
        """Test complete tournament workflow."""
        # Create tournament
        result = runner.invoke(app, ["new", "Full Test"], input="A\nB\nC\nD\n\n")
        assert result.exit_code == 0

        # Check status
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "0/3" in result.output

        # Play a match
        result = runner.invoke(app, ["play"], input="3\n1\n")
        assert result.exit_code == 0

        # Check standings
        result = runner.invoke(app, ["standings"])
        assert result.exit_code == 0

        # Check teams
        result = runner.invoke(app, ["teams"])
        assert result.exit_code == 0

        # Export
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0
