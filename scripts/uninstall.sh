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

remove_host_configs() {
    local hosts=("claude-desktop" "vscode-copilot" "codex")
    local removed_any=false

    for host in "${hosts[@]}"; do
        if [[ "$DRY_RUN" == "true" ]]; then
            action "[dry-run] Would run: sp-local-bridge-configure --remove $host"
            removed_any=true
        else
            if sp-local-bridge-configure --remove "$host" 2>/dev/null; then
                removed_any=true
            fi
        fi
    done

    if [[ "$removed_any" == "false" ]]; then
        info "No host configs to remove (or configure command unavailable)"
    fi
}

print_reminders() {
    echo
    echo "Reminders:"
    echo "  • If any host configs could not be removed automatically,"
    echo "    manually remove the superProductivity entry from your host config file."
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

    echo "Removing host configs..."
    remove_host_configs

    echo "Removing package..."
    uninstall_package

    echo "Removing skill symlink..."
    remove_skill_symlink

    print_reminders
}

main "$@"
