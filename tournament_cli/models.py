"""Data models for 2v2 Tournament."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PlayerStats:
    """Statistics for a single player."""
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0

    @property
    def games_played(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def goal_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return (self.wins / self.games_played) * 100

    def to_dict(self) -> dict:
        return {
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_scored": self.goals_scored,
            "goals_conceded": self.goals_conceded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerStats":
        return cls(
            wins=data.get("wins", 0),
            draws=data.get("draws", 0),
            losses=data.get("losses", 0),
            goals_scored=data.get("goals_scored", 0),
            goals_conceded=data.get("goals_conceded", 0),
        )


@dataclass
class Player:
    """A tournament player."""
    name: str
    stats: PlayerStats = field(default_factory=PlayerStats)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(
            name=data["name"],
            stats=PlayerStats.from_dict(data.get("stats", {})),
        )


@dataclass
class Match:
    """A 2v2 match between two teams."""
    id: int
    team1: tuple[str, str]
    team2: tuple[str, str]
    score1: Optional[int] = None
    score2: Optional[int] = None

    @property
    def played(self) -> bool:
        return self.score1 is not None and self.score2 is not None

    @property
    def winner(self) -> Optional[tuple[str, str]]:
        if not self.played:
            return None
        if self.score1 > self.score2:
            return self.team1
        elif self.score2 > self.score1:
            return self.team2
        return None  # Draw

    @property
    def loser(self) -> Optional[tuple[str, str]]:
        if not self.played:
            return None
        if self.score1 > self.score2:
            return self.team2
        elif self.score2 > self.score1:
            return self.team1
        return None  # Draw

    @property
    def is_draw(self) -> bool:
        return self.played and self.score1 == self.score2

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "team1": list(self.team1),
            "team2": list(self.team2),
            "score1": self.score1,
            "score2": self.score2,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Match":
        return cls(
            id=data["id"],
            team1=tuple(data["team1"]),
            team2=tuple(data["team2"]),
            score1=data.get("score1"),
            score2=data.get("score2"),
        )


@dataclass
class Tournament:
    """A 2v2 tournament."""
    name: str
    players: list[Player]
    matches: list[Match]
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_matches(self) -> int:
        return len(self.matches)

    @property
    def played_matches(self) -> int:
        return sum(1 for m in self.matches if m.played)

    @property
    def remaining_matches(self) -> int:
        return self.total_matches - self.played_matches

    @property
    def completion_percentage(self) -> float:
        if self.total_matches == 0:
            return 0.0
        return (self.played_matches / self.total_matches) * 100

    def get_player(self, name: str) -> Optional[Player]:
        for player in self.players:
            if player.name.lower() == name.lower():
                return player
        return None

    def get_next_match(self) -> Optional[Match]:
        for match in self.matches:
            if not match.played:
                return match
        return None

    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        for match in self.matches:
            if match.id == match_id:
                return match
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "matches": [m.to_dict() for m in self.matches],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tournament":
        return cls(
            name=data["name"],
            players=[Player.from_dict(p) for p in data["players"]],
            matches=[Match.from_dict(m) for m in data["matches"]],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
