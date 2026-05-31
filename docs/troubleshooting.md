# Troubleshooting

## Super Productivity Not Running

**Symptom:** `SP_UNAVAILABLE` error from bridge commands.

**Fix:** Start the Super Productivity desktop app. The bridge requires SP to be running.

## Local REST API Disabled

**Symptom:** Connection refused on port 3876.

**Fix:** In Super Productivity, go to **Settings → Sync & Export → Local REST API** and enable it. Restart SP if the setting was just changed.

## MCP Host Cannot Find Command

**Symptom:** Host reports "command not found" or "spawn ENOENT" for `sp-local-bridge-mcp`.

**Fix:**
1. Run `sp-local-bridge-print-config <host>` — it outputs the absolute path
2. Verify the path exists: `ls -la /path/shown/sp-local-bridge-mcp`
3. If missing, re-run `scripts/install.sh`
4. Ensure your host config uses the absolute path, not a bare command name

## GUI Host PATH Differs from Shell PATH

**Symptom:** Bridge works in terminal but host reports command not found.

**Explanation:** GUI-launched apps (VS Code, Claude Desktop) often don't inherit your shell PATH. The `sp-local-bridge-print-config` command outputs an absolute path specifically to avoid this issue.

**Fix:** Always use the absolute path from `sp-local-bridge-print-config`. If you used `--bare`, switch to the default (absolute) mode.

## Tools Not Showing in Host

**Symptom:** Host is running but no Super Productivity tools appear.

**Fix:**
1. Verify config file is saved in the correct location
2. Restart the host application completely (not just reload)
3. Check host logs for MCP server startup errors
4. Run `sp-local-bridge-doctor` to verify the bridge can start

## Host Starts but Tool Calls Fail

**Symptom:** Tools appear but return errors when invoked.

**Fix:**
1. Check if SP is running: `sp-local-bridge health`
2. Check the specific error code:
   - `SP_UNAVAILABLE` → SP not running or API disabled
   - `TIMEOUT` → SP is slow to respond, may be loading
   - `INVALID_INPUT` → check the tool parameters you're passing
   - `TASK_NOT_FOUND` → the task ID doesn't exist

## SP_UNAVAILABLE

**Cause:** The bridge cannot connect to `http://127.0.0.1:3876`.

**Possible reasons:**
- SP is not running
- Local REST API is disabled in SP settings
- SP is still starting up (wait a few seconds)

**Recovery:** Start SP and enable the API. The bridge will reconnect on the next request — no restart needed.

## TIMEOUT

**Cause:** SP did not respond within the timeout window.

**Possible reasons:**
- SP is performing a heavy sync operation
- System is under high load

**Recovery:** Wait and retry. If persistent, restart SP.

## Reinstall / Regenerate Host Config

If the bridge was reinstalled or moved:

```sh
# Regenerate config with new paths
sp-local-bridge-print-config <host>

# Update your host config file with the new snippet
# Restart the host
```

## Uninstall and Stale Config Cleanup

After uninstalling with `scripts/uninstall.sh`, remove any config snippets you added:

- **VS Code Copilot:** Remove the server entry from `.vscode/mcp.json`
- **Claude Desktop:** Remove the `super-productivity` entry from `claude_desktop_config.json`
- **Codex:** Remove the `[mcp_servers.superProductivity]` section from `~/.codex/config.toml`

Stale config entries may cause the host to log errors on startup.
