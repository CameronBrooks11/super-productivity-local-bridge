#!/usr/bin/env bash
set -euo pipefail

# Install script for Super Productivity Local Bridge.
# Installs the Python package via uv, verifies prerequisites, and prints next steps.

DRY_RUN=false
VERBOSE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install the Super Productivity Local Bridge.

Options:
  --dry-run     Print what would be done without making changes
  --verbose     Show detailed output
  -h, --help    Show this help message

Prerequisites:
  - Python 3.11+
  - uv (https://docs.astral.sh/uv/)
  - Super Productivity desktop app with Local REST API enabled
EOF
}

info() { printf "  %s\n" "$1"; }
action() { printf "  → %s\n" "$1"; }
warn() { printf "  ⚠ %s\n" "$1" >&2; }
error() { printf "  ✗ %s\n" "$1" >&2; }

check_prerequisites() {
    local ok=true

    # Check Python
    if command -v python3 &>/dev/null; then
        local py_version
        py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major minor
        major=$(echo "$py_version" | cut -d. -f1)
        minor=$(echo "$py_version" | cut -d. -f2)
        if [[ $major -ge 3 && $minor -ge 11 ]]; then
            info "✓ Python $py_version"
        else
            error "Python 3.11+ required, found $py_version"
            ok=false
        fi
    else
        error "Python 3 not found"
        ok=false
    fi

    # Check uv
    if command -v uv &>/dev/null; then
        local uv_version
        uv_version=$(uv --version 2>/dev/null | head -1)
        info "✓ $uv_version"
    else
        error "uv not found — install from https://docs.astral.sh/uv/"
        ok=false
    fi

    if [[ "$ok" != "true" ]]; then
        echo
        error "Prerequisites not met. Fix the above issues and retry."
        exit 1
    fi
}

install_package() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    if [[ "$DRY_RUN" == "true" ]]; then
        action "[dry-run] Would install sp-local-bridge from: $script_dir"
        action "[dry-run] Command: uv tool install --from \"$script_dir\" sp-local-bridge"
    else
        action "Installing sp-local-bridge..."
        if uv tool install --from "$script_dir" sp-local-bridge 2>/dev/null; then
            info "✓ sp-local-bridge installed"
        else
            # May already be installed — try upgrade
            if uv tool upgrade --from "$script_dir" sp-local-bridge 2>/dev/null; then
                info "✓ sp-local-bridge upgraded"
            else
                warn "Could not install via 'uv tool'. Try: uv pip install -e '$script_dir'"
                return 1
            fi
        fi
    fi
}

verify_install() {
    if [[ "$DRY_RUN" == "true" ]]; then
        action "[dry-run] Would verify: sp-local-bridge --version"
        action "[dry-run] Would verify: sp-local-bridge-doctor"
        return
    fi

    if command -v sp-local-bridge &>/dev/null; then
        local version
        version=$(sp-local-bridge --version 2>/dev/null || echo "unknown")
        info "✓ sp-local-bridge $version"
    else
        warn "sp-local-bridge not on PATH after install"
        warn "You may need to add ~/.local/bin to your PATH"
    fi
}

print_next_steps() {
    echo
    echo "Next steps:"
    echo "  1. Enable Local REST API in Super Productivity: Settings → Misc"
    echo "  2. Run: sp-local-bridge-doctor"
    echo "  3. For MCP host config: sp-local-bridge-print-config claude-desktop"
    echo
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run) DRY_RUN=true; shift ;;
            --verbose) VERBOSE=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) error "Unknown option: $1"; usage; exit 2 ;;
        esac
    done

    echo "sp-local-bridge install"
    echo "========================"
    echo

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[dry-run mode — no changes will be made]"
        echo
    fi

    echo "Checking prerequisites..."
    check_prerequisites
    echo

    echo "Installing..."
    install_package
    echo

    echo "Verifying..."
    verify_install

    print_next_steps
}

main "$@"
