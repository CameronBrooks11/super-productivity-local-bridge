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

print_reminders() {
    echo
    echo "Reminders:"
    echo "  • Remove the MCP server entry from your host config if configured:"
    echo "    - Claude Desktop: ~/.config/Claude/claude_desktop_config.json"
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

    print_reminders
}

main "$@"
