# Super Productivity Local Bridge — Setup

You are setting up the Super Productivity Local Bridge, an MCP server that gives
AI agents access to the Super Productivity desktop app's task management
(create/update/complete tasks, list projects and tags, etc.) via its Local REST API.

Follow all phases in order. Do not skip phases. Do not ask the user questions
except at the single checkpoint in Phase 2.

---

## Phase 1: Discovery (silent — do not print findings yet)

Run these checks silently and collect the results:

1. **Python version** — run `python3 --version`. Requires 3.11+.
2. **uv installed** — run `uv --version`. Required for installation.
3. **SP app running** — run `curl -sf http://127.0.0.1:3876/health`. If it
   fails, the Super Productivity desktop app is not running or Local REST API is
   not enabled.
4. **Already installed** — run `sp-local-bridge-mcp --help 2>/dev/null`. If it
   succeeds, the bridge is already installed.
5. **Detect platform** — check `uname -s` (Linux/Darwin) and `uname -m`.
6. **Detect agent** — determine which agent you are running as:
   - If `$VSCODE_PID` or `$VSCODE_IPC_HOOK_CLI` is set → vscode-copilot
   - If `codex --version` succeeds → codex
   - Otherwise → unknown (will ask user which host to configure)
7. **Existing config** — if installed, run `sp-local-bridge-configure --dry-run <detected-host>`
   to check if config is already written.
8. **Skills symlink** — check if `~/.agents/skills/sp-local-bridge-setup` exists.

---

## Phase 2: Plan (single interactive checkpoint)

Present ALL findings from Phase 1 in a clear summary table:

```
Prerequisite        Status
─────────────────────────────────
Python 3.11+        ✓ 3.11.x / ✗ not found
uv                  ✓ 0.x.x / ✗ not found
SP app              ✓ reachable / ✗ not running
Bridge installed    ✓ version / ✗ not installed
Host detected       vscode-copilot / claude-desktop / codex / unknown
Config written      ✓ / ✗
Skills symlink      ✓ / ✗
```

Then state the proposed actions:
- Install bridge (if not installed)
- Configure host (if not configured)
- Create skills symlink (if missing)

Ask the user: **"Proceed with setup? [Y/n]"**

If any prerequisite is missing (Python, uv), tell the user what to install and stop.
If SP app is not running, warn but offer to proceed (config can be written without SP running).

---

## Phase 3: Execute (uninterrupted after confirmation)

### 3a. Install the bridge (if not already installed)

Determine the repo root (the directory containing this SKILL.md, two levels up):

```bash
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
```

If not installed, run:

```bash
cd "$REPO_ROOT" && scripts/install.sh
```

If already installed, skip.

### 3b. Configure the detected host

Run the configure command:

```bash
sp-local-bridge-configure <detected-host>
```

Where `<detected-host>` is one of: `vscode-copilot`, `claude-desktop`, `codex`.

If the host could not be detected, ask the user which host to configure.

### 3c. Create skills symlink

```bash
mkdir -p ~/.agents/skills
ln -sfn "$REPO_ROOT/skills/sp-local-bridge-setup" ~/.agents/skills/sp-local-bridge-setup
```

---

## Phase 4: Verify

Run the doctor command:

```bash
sp-local-bridge-doctor
```

All checks should pass. If SP connectivity fails, remind the user to:
1. Open Super Productivity desktop app
2. Enable Local REST API: Settings → Misc → Enable Local REST API
3. Re-run doctor

---

## Phase 5: Report

Print a final summary:

```
Setup complete
──────────────
Bridge:     installed (sp-local-bridge v0.1.1)
Host:       <host> configured
Config:     <path-to-config-file>
Skills:     ~/.agents/skills/sp-local-bridge-setup → linked
SP status:  ✓ connected / ⚠ not running (configure host when ready)

Available tools (13):
  task.list, task.get, task.create, task.update, task.complete,
  task.start, task.stop, task.archive, task.restore,
  project.list, tag.list, bridge.health

Next: try asking me to "list my tasks" or "create a task called Test".
```
