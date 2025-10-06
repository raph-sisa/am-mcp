Project Summary
Goal: Build a Python-based Hybrid MCP for Apple Music that lets ChatGPT or Claude Desktop discover, play, and manage music.
This MCP will:

Use MusicKit API for search, metadata, and catalog access.

Use AppleScript for local playback control on macOS.

Expose six core actions through a manifest for conversational control.

# Apple Music MCP — Phased Task List

> Scope: Python-based hybrid MCP for Apple Music. MusicKit for catalog search/metadata. AppleScript for local playback. Targets ChatGPT/Claude Desktop.

---

## Phase 0 — Access and Prerequisites

### 0.1 Apple Developer and Media Services
- [ ] Enroll in Apple Developer Program (paid).
- [ ] Create Media ID: **Identifier** `media.xyz.inwonder.applemusic.mcp` and **Description** (e.g., InWonder Music Control).
- [ ] Create Media Services private key linked to the Media ID.
- [ ] Choose **Key Name** using only letters/numbers (e.g., `MSKInwonderAppleMusicMcpProd202510`). Record Apple-assigned **Key ID**.
- [ ] Securely store `.p8` key. Restrict permissions.

### 0.2 Local Environment
- [ ] macOS 12+ with Apple Music app installed and signed in with an Apple Music subscription.
- [ ] Install Python 3.10+ and Git.
- [ ] Enable macOS Automation for Terminal/IDE (Privacy & Security → Automation).
- [ ] Create project directory.

### 0.3 Configuration
- [ ] Create `.env` with:
  - `TEAM_ID`
  - `KEY_ID`
  - `PRIVATE_KEY_PATH` (to `.p8`)
  - `STOREFRONT` (e.g., `us`)
- [ ] Prepare `.env.example` (no secrets) and `.gitignore` entries.

### 0.4 Preflight Verification
- [ ] AppleScript probe: `osascript -e 'tell application "Music" to playpause'`.
- [ ] Developer token mint test (ES256). 
- [ ] Catalog search curl test with dev token returns 200 JSON.

**Go criteria**
- [ ] AppleScript probe works.
- [ ] Catalog search succeeds with dev token.

---

## Phase 1 — Foundation and Architecture

### 1.1 Repo and Tooling
- [ ] Initialize repo `apple-music-mcp` (Poetry or venv).
- [ ] Add deps: `requests`, `pydantic` or `jsonschema`, `pyjwt`, `python-dotenv`.
- [ ] Add Makefile or task runner (`make test`, `make run`, `make lint`).

### 1.2 Project Structure
```
apple-music-mcp/
  manifest.json
  main.py
  handlers/
    search.py
    play.py
    playback.py
    queue.py
    library.py
    playlist.py
  utils/
    apple_script.py
    auth.py
  tests/
  README.md
```

### 1.3 Manifest
- [ ] Define tools and IO schemas:
  - `search_music`
  - `play_song`
  - `control_playback` (pause/resume/next/previous/shuffle/repeat)
  - `manage_queue` (add/view/clear)
  - `add_to_library` / `remove_from_library` (local scope)
  - `create_playlist`
- [ ] Validate against host MCP expectations.

### 1.4 Dispatcher and Health
- [ ] Implement dispatcher in `main.py` with strict validation (`extra=forbid`).
- [ ] Add `mcp.health_check` tool:
  - AppleScript playpause probe
  - MusicKit search probe

### 1.5 Logging and Error Model
- [ ] Structured logs with request IDs.
- [ ] Standard error shape `{code, message, hint}`. Redact tokens.

**Go criteria**
- [ ] MCP host lists tools and can call `mcp.health_check` successfully.

---

## Phase 2 — Core Functionality

### 2.1 AppleScript Control (Local)
- [ ] `utils/apple_script.py`: `run_applescript(cmd: str)` with robust error capture.
- [ ] `handlers/playback.py`: `play`, `pause`, `next`, `previous`, `shuffle`, `repeat`.
- [ ] `handlers/queue.py`: minimal `add_to_queue(url|track)`, `view_queue` if supported.
- [ ] `handlers/library.py`: local add/remove where feasible.
- [ ] Auto-launch Music if not running. Detect and report permission errors with clear hints.

### 2.2 MusicKit Integration (Catalog)
- [ ] `utils/auth.py`: developer token minting (ES256), clock skew tolerance.
- [ ] `handlers/search.py`: `GET /v1/catalog/{storefront}/search` with `term`, `types`, `limit`, `offset`.
- [ ] Normalized result schema: id, name, artist, album, url, artwork, kind.
- [ ] Bounded retries with jitter for 5xx; cache hot results.

### 2.3 Hybrid Flow
- [ ] Resolve search → choose best match.
- [ ] Prefer `open location <apple music url>` for immediate playback.
- [ ] Fallbacks: add to library then play; or return URL with actionable message.
- [ ] Unified success payload with now playing metadata.

### 2.4 Security and Config
- [ ] Never log secrets. Token lifetime ≤ 6 months. Plan rotation.
- [ ] Config precedence: request args → env → defaults.

**Go criteria**
- [ ] End-to-end: “search → play” works for a known track.
- [ ] Playback controls respond locally.

---

## Phase 3 — Polishing, Testing, Documentation

### 3.1 Tests
- [ ] Unit tests for handlers (mock subprocess/HTTP).
- [ ] Integration tests on macOS runner for AppleScript.
- [ ] Contract tests for manifest tool IO.

### 3.2 Docs
- [ ] README: setup, `.env`, run, tool examples, troubleshooting.
- [ ] Auth guide: Media ID, key creation, token minting, rotation policy.
- [ ] Permission guide: macOS Automation prompts with screenshots.

### 3.3 Packaging and Quality
- [ ] Pre-commit hooks: formatting, `git-secrets`.
- [ ] Version bump and changelog.
- [ ] Optional: Homebrew or simple installer script.

### 3.4 Optional Enhancements
- [ ] `now_playing` tool.
- [ ] Lyrics retrieval if available.
- [ ] Caching layer toggle.
- [ ] Multi-env keys (dev/prod) with toggle.

**Go criteria**
- [ ] Clean install on a new Mac reproduces Phase 2 success using only the docs.
