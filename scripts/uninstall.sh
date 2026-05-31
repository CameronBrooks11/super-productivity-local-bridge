#!/usr/bin/env bash
set -euo pipefail

# Uninstall script for Super Productivity Local Bridge.
# Removes the installed package and reminds about host config cleanup.

DRY_RUN=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Uninstall the Super Productivity Local Bridge.

Options:
  --dry-run     Print what would be done without making changes
  -h, --help    Show this help message
EOF
}

info() { printf "  %s\n" "$1"; }
action() { printf "  → %s\n" "$1"; }
warn() { printf "  ⚠ %s\n" "$1" >&2; }

uninstall_package() {
    if [[ "$DRY_RUN" == "true" ]]; then
        action "[dry-run] Would run: uv tool uninstall sp-local-bridge"
    else
        if uv tool uninstall sp-local-bridge 2>/dev/null; then
            info "✓ sp-local-bridge uninstalled"
        else
            warn "sp-local-bridge was not installed via 'uv tool' (or already removed)"
            info "If installed via pip: pip uninstall sp-local-bridge"
        fi
    fi
}

remove_skill_symlink() {
    local skill_link="$HOME/.agents/skills/sp-local-bridge-setup"

    if [[ ! -L "$skill_link" && ! -e "$skill_link" ]]; then
        info "No skill symlink at $skill_link"
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        action "[dry-run] Would remove symlink: $skill_link"
    else
        rm -f "$skill_link"
        info "✓ Skill symlink removed: $skill_link"
    fi
}

print_reminders() {
    echo
    echo "Reminders:"
    echo "  • Remove MCP host config entries:"
    echo "    sp-local-bridge-configure --remove claude-desktop"
    echo "    sp-local-bridge-configure --remove vscode-copilot"
    echo "    sp-local-bridge-configure --remove codex"
    echo "  • Or manually remove from your host config file."
    echo "  • The Super Productivity desktop app and its data are not affected."
    echo
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run) DRY_RUN=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) warn "Unknown option: $1"; usage; exit 2 ;;
        esac
    done

    echo "sp-local-bridge uninstall"
    echo "=========================="
    echo

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[dry-run mode — no changes will be made]"
        echo
    fi

    echo "Removing package..."
    uninstall_package

    echo "Removing skill symlink..."
    remove_skill_symlink

    print_reminders
}

main "$@"
