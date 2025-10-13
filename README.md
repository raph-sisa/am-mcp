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
│   ├── musickit.py
│   └── exceptions.py
├── tests/
│   ├── test_auth.py
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
| `search_music` | Discover catalog items using MusicKit. | Normalizes song metadata, caches results, and retries transient failures. |
| `play_song` | Launch playback of a track. | Fetches catalog metadata, resolves playback URLs, and triggers AppleScript playback. |
| `control_playback` | Manage playback state (play, pause, skip, shuffle, repeat). | Sends concrete AppleScript commands with shuffle/repeat state toggles. |
| `manage_queue` | Add to, view, or clear the Apple Music play queue. | Uses AppleScript to add songs, inspect the queue, and clear items. |
| `add_to_library` / `remove_from_library` | Manage the local library. | Adds or removes tracks via AppleScript, using MusicKit metadata for matching. |
| `create_playlist` | Create playlists seeded with catalog tracks. | Builds/refreshes playlists and injects catalog songs via AppleScript automation. |
| `mcp.health_check` | Probe AppleScript and MusicKit readiness. | Executes a play/pause probe and MusicKit search, returning per-check diagnostics. |

Each tool enforces strict argument validation with explicit type and bounds checks, returning standardized success or error payloads (`{code, message, hint}` on failure).

## Development Tasks
- `make lint` — Static analysis with Ruff.
- `make test` — Run unit tests (pytest) covering dispatcher validation and error handling.
- `make check` — Run linting and tests together.
- `make format` — Apply import sorting and formatting (Ruff).

## Testing Strategy
Unit tests include:
- `tests/test_dispatcher.py` validating dispatcher error paths.
- `tests/test_auth.py` covering configuration loading, JWT minting, and caching safeguards.

Future test work includes:
- Mocked AppleScript execution for playback flows.
- HTTP-layer contract tests for MusicKit interactions.
- Integration tests on a macOS runner validating end-to-end “search → play”.

## Troubleshooting & Permissions
- Grant automation privileges to your terminal or IDE when macOS prompts for Apple Music control.
- Ensure the Apple Music app is running and logged in with an active subscription.
- Review [`docs/permissions.md`](docs/permissions.md) for step-by-step screenshots and remediation tips.

## Roadmap
- Extend queue inspection to return structured metadata instead of string summaries.
- Implement additional error telemetry for AppleScript failures (e.g., Automation permission prompts).
- Provide a `now_playing` optional tool once playback metadata is accessible.
- Expand documentation with setup videos or quick-start scripts (e.g., Homebrew formula) when the core flows are stable.
