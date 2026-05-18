# Nikke PVP Arena Match Analyzer

Arena team analysis tool for NIKKE: Goddess of Victory. Built as a Claude Code skill — provides **charge calculation**, **historical match matching**, and **match recording**.

## Features

| Feature | Description |
|---------|-------------|
| **Match Query** | Resolve team nicknames to full roster, calculate burst chains and charge speed, find historical matches with scoring |
| **Match Recorder** | Convert unstructured match descriptions into validated TOML entries |
| **Alias Mapping** | Character nickname → full name resolution with conflict handling |

## Project Structure

```
nikke-pvp/
├── SKILL.md                          # Skill entry point and routing
├── config.toml                       # Path and charge phase configuration
├── references/                       # Character roster, charge speed data
├── scripts/                          # Charge calc, burst chain, validation
└── sub-skills/
    ├── query/                        # Match query (incl. match_finder.py)
    ├── match_recorder/               # Match recording
    └── alias_mapping/                # Nickname resolution
```

See [STRUCTURE.md](STRUCTURE.md) for full details.

## Quick Start

### Query a team

```bash
python3 sub-skills/query/query_output.py "team_nickname_string"
```

Outputs 4 sections: query results → charge calculation → historical matches → team analysis.

### Record a match

```bash
python3 sub-skills/match_recorder/match_recorder.py \
    "defender_team_nicknames" "attacker_team_nicknames" \
    --result defender_win --source self
```

## Tech Stack

- **Data format**: TOML (single data source, `matches.toml`)
- **Runtime**: Python 3.13+ (executed within Claude Agent skills)


## License

MIT
