"""JSON persistence layer for tournaments."""

import json
from pathlib import Path
from typing import Optional
from tournament_cli.models import Tournament


# Default tournaments directory
TOURNAMENTS_DIR = Path(__file__).parent.parent / "tournaments"
CONFIG_FILE = TOURNAMENTS_DIR / ".config.json"


def ensure_tournaments_dir() -> Path:
    """Ensure the tournaments directory exists."""
    TOURNAMENTS_DIR.mkdir(parents=True, exist_ok=True)
    return TOURNAMENTS_DIR


def get_config() -> dict:
    """Get the config file contents."""
    ensure_tournaments_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """Save the config file."""
    ensure_tournaments_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_current_tournament_name() -> Optional[str]:
    """Get the name of the currently active tournament from config."""
    config = get_config()
    return config.get("current_tournament")


def set_current_tournament_name(name: Optional[str]) -> None:
    """Set the currently active tournament name in config."""
    config = get_config()
    if name:
        config["current_tournament"] = name
    elif "current_tournament" in config:
        del config["current_tournament"]
    save_config(config)


def get_tournament_path(name: str) -> Path:
    """Get the path for a tournament file."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return ensure_tournaments_dir() / f"{safe_name}.json"


def save_tournament(tournament: Tournament) -> Path:
    """Save a tournament to a JSON file."""
    path = get_tournament_path(tournament.name)
    with open(path, "w") as f:
        json.dump(tournament.to_dict(), f, indent=2)
    return path


def load_tournament(name: str) -> Optional[Tournament]:
    """Load a tournament from a JSON file."""
    path = get_tournament_path(name)
    if not path.exists():
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return Tournament.from_dict(data)


def list_tournaments() -> list[str]:
    """List all saved tournament names."""
    ensure_tournaments_dir()
    tournaments = []
    for path in TOURNAMENTS_DIR.glob("*.json"):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            tournaments.append(data["name"])
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(tournaments)


def delete_tournament(name: str) -> bool:
    """Delete a tournament file."""
    path = get_tournament_path(name)
    if path.exists():
        path.unlink()
        return True
    return False


# Current tournament state (in-memory cache)
_current_tournament: Optional[Tournament] = None


def get_current_tournament() -> Optional[Tournament]:
    """Get the currently loaded tournament."""
    global _current_tournament
    if _current_tournament:
        return _current_tournament
    # Try to load from config
    name = get_current_tournament_name()
    if name:
        _current_tournament = load_tournament(name)
    return _current_tournament


def set_current_tournament(tournament: Optional[Tournament]) -> None:
    """Set the currently loaded tournament."""
    global _current_tournament
    _current_tournament = tournament
    set_current_tournament_name(tournament.name if tournament else None)


def save_current_tournament() -> Optional[Path]:
    """Save the current tournament to disk."""
    tournament = get_current_tournament()
    if tournament:
        return save_tournament(tournament)
    return None
