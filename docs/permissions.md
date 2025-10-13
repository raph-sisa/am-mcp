# AppleScript Permissions Guide

AppleScript control of the Music app requires explicit user consent on macOS. Follow these steps to avoid automation failures.

## 1. Initial Prompt
When the MCP first attempts to run an AppleScript command (e.g., `playpause`), macOS presents a dialog asking to allow Terminal/IDE to control Music. Click **OK**.

If you clicked **Don't Allow**, grant permission manually as described below.

## 2. Grant Automation Access Manually
1. Open **System Settings → Privacy & Security → Automation**.
2. Locate your terminal application (e.g., Terminal, iTerm, VS Code) in the list.
3. Enable the checkbox next to **Music** for that application.
4. Restart the terminal/IDE to ensure the permission takes effect.

## 3. Troubleshooting
- **Prompt does not appear:** Run a simple probe: `osascript -e 'tell application "Music" to playpause'`. The prompt should surface if permissions are missing.
- **Automation denied errors:** Remove the app from the Automation list, restart macOS, and trigger the prompt again.
- **Multiple terminals/IDEs:** Each application requesting automation access must be approved individually.
- **Headless environments:** AppleScript requires an interactive macOS session; remote or CI execution must use a logged-in user session (consider macOS runners with GUI access).

## 4. Logging Recommendations
- Log permission-related failures using the standardized `{code, message, hint}` shape so hosts can provide actionable instructions.
- Avoid logging full AppleScript source when it contains sensitive values.

Ensuring automation permissions are correctly configured allows the MCP to drive the Music app reliably.
