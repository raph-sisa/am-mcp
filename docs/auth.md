# MusicKit Authentication Guide

This document outlines how to provision credentials and generate developer tokens for the Apple Music MCP.

## 1. Provision Media Services Credentials
1. Sign in to the [Apple Developer](https://developer.apple.com/) portal using an account enrolled in the paid program.
2. Navigate to **Certificates, Identifiers & Profiles → Identifiers** and add a new **Media ID**.
   - Identifier suggestion: `media.xyz.inwonder.applemusic.mcp`
   - Description example: `InWonder Music Control`
3. Under **Keys**, create a Media Services private key.
   - Use an alphanumeric name only (e.g., `MSKInwonderAppleMusicMcpProd202510`).
   - Record the Apple-assigned Key ID and download the `.p8` key once (Apple only serves it once).
4. Store the `.p8` file securely with restricted permissions. The MCP expects to read it from the path referenced by `PRIVATE_KEY_PATH`.

## 2. Environment Variables
Populate `.env` (see `.env.example`) with:

```
TEAM_ID=ABCDE12345
KEY_ID=12ABCD34EF
PRIVATE_KEY_PATH=/Users/you/keys/AuthKey_12ABCD34EF.p8
STOREFRONT=us
```

- `TEAM_ID`: 10-character Apple Developer Team ID.
- `KEY_ID`: The Key ID assigned to the Media Services key.
- `PRIVATE_KEY_PATH`: Absolute path to the downloaded `.p8` key.
- `STOREFRONT`: Apple Music storefront (e.g., `us`, `gb`, `jp`).

## 3. Token Generation Workflow
1. Load configuration using `utils.auth.load_config()` to validate that environment variables exist.
2. Read the private key contents from `PRIVATE_KEY_PATH` (restrict file permissions to the owning user).
3. Build an ES256 JWT with the following claims:
   - `iss`: Your `TEAM_ID`
   - `iat`: Current UNIX timestamp
   - `exp`: Timestamp no more than 6 months in the future
   - `kid`: The `KEY_ID` header parameter
4. Sign with the private key using `PyJWT`:

```python
import jwt
from datetime import datetime, timedelta, timezone

headers = {"alg": "ES256", "kid": config.key_id}
claims = {
    "iss": config.team_id,
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(hours=12),
}
token = jwt.encode(claims, private_key, algorithm="ES256", headers=headers)
```

5. Use the resulting developer token for MusicKit requests (e.g., `Authorization: Bearer <token>`).

## 4. Rotation and Security Considerations
- Keep token lifetimes short (≤ 6 months) and regenerate well before expiry.
- Rotate private keys periodically and revoke unused keys in the Apple Developer portal.
- Never log tokens or private key contents. Sanitize debug logs before sharing externally.
- Consider storing secrets in macOS Keychain or a secrets manager for production deployments.

## 5. Preflight Verification
Before enabling tools for end users, confirm:
- `osascript -e 'tell application "Music" to playpause'` works without errors.
- A MusicKit catalog search using `curl` and your developer token returns a `200` response.

Following these steps ensures the MCP can authenticate with MusicKit and control Apple Music reliably.
