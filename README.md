# Apple Music MCP

A Python-based Hybrid Model Context Protocol (MCP) server that allows ChatGPT or Claude Desktop to search, play, and manage music through Apple Music. The project combines MusicKit catalog access with local AppleScript playback control on macOS.

## Project Goals
- Discover catalog metadata via the MusicKit API.
- Control the local Apple Music app using AppleScript.
- Expose conversational tools for search, playback, queue, library, and playlist management, plus a health check.

## Repository Layout
```
apple-music-mcp/
├── Makefile
├── manifest.json
├── main.py
├── handlers/
│   ├── health.py
│   ├── library.py
│   ├── play.py
│   ├── playback.py
│   ├── playlist.py
│   ├── queue.py
│   └── search.py
├── utils/
│   ├── apple_script.py
│   ├── auth.py
│   └── exceptions.py
├── tests/
│   └── test_dispatcher.py
├── .env.example
└── docs/
    ├── auth.md
    └── permissions.md
```

## Prerequisites
1. **Apple Developer Access**
   - Enroll in the Apple Developer Program (paid tier).
   - Create a Media Services identifier (e.g., `media.xyz.inwonder.applemusic.mcp`).
   - Generate a Media Services private key (`.p8`) associated with the identifier and capture the Key ID.
2. **macOS Host Requirements**
   - macOS 12 or later with the Apple Music app installed and signed into an Apple Music subscription.
   - Enable Terminal (or IDE) under *System Settings → Privacy & Security → Automation* so AppleScript can control Music.
3. **Development Environment**
   - Python 3.10 or newer.
   - [Poetry](https://python-poetry.org/) for dependency management.
   - Git, Make, and the Apple Music app (for runtime testing).

## Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/apple-music-mcp.git
   cd apple-music-mcp
   ```
2. **Copy and populate environment variables**
   ```bash
   cp .env.example .env
   ```
   Update the newly created `.env` with your `TEAM_ID`, `KEY_ID`, `PRIVATE_KEY_PATH`, and desired `STOREFRONT` (e.g., `us`).
3. **Install dependencies**
   ```bash
   make install
   ```
4. **Run the MCP server**
   ```bash
   make run
   ```
   The entry point currently accepts JSON requests over STDIN/STDOUT. Integrate the dispatcher with your host MCP runtime to expose the manifest-defined tools.

## Configuration
- Secrets remain in `.env` and are never committed thanks to `.gitignore` safeguards.
- `python-dotenv` automatically loads `.env` when `main.py` executes, allowing overrides through real environment variables.
- See [`docs/auth.md`](docs/auth.md) for end-to-end credential guidance and token rotation notes.

## Tools Overview
| Tool | Purpose | Notes |
| ---- | ------- | ----- |
| `search_music` | Discover catalog items using MusicKit. | Validates query, result schema TBD. |
| `play_song` | Launch playback of a track. | Hybrid flow via AppleScript and MusicKit metadata. |
| `control_playback` | Manage playback state (play, pause, skip, shuffle, repeat). | Designed to drive AppleScript commands. |
| `manage_queue` | Add to, view, or clear the Apple Music play queue. | Supports `add`, `view`, and `clear` intents. |
| `add_to_library` / `remove_from_library` | Manage the local library. | Requires MusicKit and local sync. |
| `create_playlist` | Create playlists seeded with catalog tracks. | Accepts optional descriptions and initial track IDs. |
| `mcp.health_check` | Probe AppleScript and MusicKit readiness. | Performs combined diagnostics before exposing other tools. |

Each tool enforces strict argument validation (`pydantic` with `extra=forbid`) and returns standardized success or error payloads (`{code, message, hint}` on failure).

## Development Tasks
- `make lint` — Static analysis with Ruff.
- `make test` — Run unit tests (pytest) covering dispatcher validation and error handling.
- `make check` — Run linting and tests together.
- `make format` — Apply import sorting and formatting (Ruff).

## Testing Strategy
Current unit tests live in `tests/test_dispatcher.py` and assert:
- Unknown tools return an `unknown_tool` error.
- Invalid arguments trigger `invalid_arguments` with descriptive hints.
- The health check rejects unexpected payloads.

Future test work includes:
- Mocked AppleScript execution for playback flows.
- HTTP-layer contract tests for MusicKit interactions.
- Integration tests on a macOS runner validating end-to-end “search → play”.

## Troubleshooting & Permissions
- Grant automation privileges to your terminal or IDE when macOS prompts for Apple Music control.
- Ensure the Apple Music app is running and logged in with an active subscription.
- Review [`docs/permissions.md`](docs/permissions.md) for step-by-step screenshots and remediation tips.

## Roadmap
- Implement real AppleScript helpers that gracefully handle app launch, permission denials, and error reporting.
- Add MusicKit authentication utilities for ES256 token minting and catalog search with retry/backoff.
- Provide a `now_playing` optional tool once playback metadata is accessible.
- Expand documentation with setup videos or quick-start scripts (e.g., Homebrew formula) when the core flows are stable.
