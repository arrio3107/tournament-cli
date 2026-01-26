# Tournament CLI

A command-line tool for managing tournaments with flexible team sizes (1v1, 2v2, 1v2, 3v3, and more). Originally built for FIFA gaming sessions with friends, but works for any competition format.

This project is in large parts coded by Claude Code (Opus 4.5).

## Features

- **Flexible matchmaking**: Supports 1v1, 2v2, 1v2 (handicap), 3v3, and custom modes. Automatically generates all possible matchups where every player plays with and against everyone else
- **Player standings**: Track wins, draws, losses, goals, and points with automatic ranking
- **Team rankings**: See which player pairings perform best together
- **Player statistics**: Detailed stats including partnership performance with each teammate
- **Export**: Generate tournament summaries in Markdown or styled PDF format

## Installation

### From GitHub Releases (Recommended)

Download the latest binary for your platform from the [Releases](https://github.com/strehk/tournament-cli/releases) page:

- **macOS (Apple Silicon)**: `tournament-cli-macos-arm64`
- **macOS (Intel)**: `tournament-cli-macos-x86_64`
- **Linux**: `tournament-cli-linux-x86_64`
- **Windows**: `tournament-cli-windows-x86_64.exe`

Make the binary executable (macOS/Linux):

```bash
chmod +x tournament-cli-*
./tournament-cli-macos-arm64 --help
```

### From Source

Requires Python 3.9+

```bash
git clone https://github.com/strehk/tournament-cli.git
cd tournament-cli
pip install -e .
```

## Quick Start

### 1. Create a tournament

```bash
tournament-cli new "Game Night"
```

You'll be prompted to enter player names (minimum 4 players).

### 2. Play matches

```bash
tournament-cli play
```

This shows the next match and prompts for scores. You can also play a specific match:

```bash
tournament-cli play 5  # Play match #5
```

### 3. View standings

```bash
tournament-cli standings
```

### 4. View team rankings

```bash
tournament-cli teams
```

### 5. Export results

```bash
tournament-cli export           # Markdown
tournament-cli export --pdf     # PDF
```

## Usage Examples

Real-world scenarios for your gaming sessions.

### Classic 2v2 with 4 Players

Friday FIFA night with the usual crew. Everyone plays with and against everyone.

```bash
tournament-cli new "Friday FIFA" --mode 2v2
# Enter: Marcus, Dennis, Kevin, Steve
```

3 matches total - perfect for a quick session.

### 2v2 with 5 Players (One Sits Out)

Fifth wheel shows up uninvited. Someone rotates out each match.

```bash
tournament-cli new "Awkward Fifth" --mode 2v2
```

15 matches total - the CLI handles rotation automatically.

### 1v2 Handicap Mode (3 Players)

That one friend who's "too good" plays solo against a duo. Nobody waits, everyone plays every match.

```bash
tournament-cli new "Humble Marcus" --mode 1v2
# Enter 3 players - great for uneven skill levels
```

### 1v1 Duel (2 Players)

Just two rivals settling the score. No teammates to blame.

```bash
tournament-cli new "The Reckoning" --mode 1v1
# Single match, winner takes bragging rights
```

### 1v1 with Pre-formed Teams (Workaround)

Couples tournament - 4 pairs compete as units.

**Trick:** Enter team names as "players" instead of individual names.

```bash
tournament-cli new "Couples Clash" --mode 1v1
# Enter team names: "Tom+Sarah", "The Couch Potatoes", "Team No Sleep", etc.
```

### 3v3 Mode (6 Players)

Rocket League night - full 3v3 chaos.

```bash
tournament-cli new "Rocket Night" --mode 3v3
# Everyone plays with and against everyone
```

### Double Header (--rounds 2)

Nobody wants the night to end. Run the whole schedule twice.

```bash
tournament-cli new "Marathon Night" --mode 2v2 --rounds 2
# Use `add-round` mid-tournament if you decide to extend
```

## Commands Reference

| Command          | Description                     |
| ---------------- | ------------------------------- |
| `new <name>`     | Create a new tournament         |
| `list`           | List all saved tournaments      |
| `load <name>`    | Load an existing tournament     |
| `status`         | Show tournament overview        |
| `schedule`       | Show all matches                |
| `schedule -r`    | Show only remaining matches     |
| `play [id]`      | Record a match result           |
| `standings`      | Show player rankings            |
| `teams`          | Show team (pair) rankings       |
| `stats <player>` | Show detailed player statistics |
| `reset`          | Reset all match results         |
| `export`         | Export to Markdown              |
| `export --pdf`   | Export to PDF                   |

## How It Works

For a 2v2 tournament with `n` players, the CLI generates all possible matchups where:

- Every player plays **with** every other player as teammates
- Every player plays **against** every other player as opponents

Total matches = `n(n-1)(n-2)(n-3) / 8`

| Players | Matches |
| ------- | ------- |
| 4       | 3       |
| 5       | 15      |
| 6       | 45      |
| 7       | 105     |
| 8       | 210     |

## Scoring

- **Win**: 3 points
- **Draw**: 1 point
- **Loss**: 0 points

Rankings are sorted by: Points > Goal Difference > Goals Scored

## Development

### Setup

```bash
git clone https://github.com/strehk/tournament-cli.git
cd tournament-cli
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e .
```

### Running

```bash
tournament-cli --help
```

### Building Binaries

```bash
pip install pyinstaller
pyinstaller tournament-cli.spec
```

The binary will be in `dist/tournament-cli`.

## License

MIT License - see [LICENSE](LICENSE) for details.
