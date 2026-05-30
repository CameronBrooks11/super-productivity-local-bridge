#!/usr/bin/env bash
set -euo pipefail

# Install script for Super Productivity Local Bridge.
# Installs the Python package via uv, verifies commands are accessible, and prints next steps.

DRY_RUN=false
VERBOSE=false
INSTALL_OK=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

# Resolve the uv tool bin directory (where executables are placed)
resolve_tool_bin_dir() {
    # uv tool dir gives the tool environment root; bin is alongside at ../bin
    # But the canonical way is to check UV_TOOL_BIN_DIR or default
    if [[ -n "${UV_TOOL_BIN_DIR:-}" ]]; then
        echo "$UV_TOOL_BIN_DIR"
    else
        # Default location per uv docs
        echo "${HOME}/.local/bin"
    fi
}

install_package() {
    if [[ "$DRY_RUN" == "true" ]]; then
        action "[dry-run] Would install sp-local-bridge from: $SCRIPT_DIR"
        action "[dry-run] Command: uv tool install --reinstall --from \"$SCRIPT_DIR\" sp-local-bridge"
    else
        action "Installing sp-local-bridge..."
        # Always use --reinstall to guarantee a fresh build from source.
        # Without it, uv may reuse a cached wheel for the same version string.
        local uv_output
        if uv_output=$(uv tool install --reinstall --from "$SCRIPT_DIR" sp-local-bridge 2>&1); then
            info "✓ sp-local-bridge installed (fresh build)"
            if [[ "$VERBOSE" == "true" ]]; then
                info "$uv_output"
            fi
        else
            error "Could not install via 'uv tool install'."
            error "Try manually: cd '$SCRIPT_DIR' && uv tool install --reinstall --from . sp-local-bridge"
            if [[ "$VERBOSE" == "true" ]]; then
                error "uv output:"
                printf "%s\n" "$uv_output" >&2
            else
                error "Re-run with --verbose for details."
            fi
            exit 1
        fi
    fi
}

verify_install() {
    if [[ "$DRY_RUN" == "true" ]]; then
        local bin_dir
        bin_dir=$(resolve_tool_bin_dir)
        action "[dry-run] Would verify commands in: $bin_dir"
        action "[dry-run] Would check: sp-local-bridge, sp-local-bridge-mcp, sp-local-bridge-doctor, sp-local-bridge-print-config"
        return
    fi

    local bin_dir
    bin_dir=$(resolve_tool_bin_dir)
    local commands=(sp-local-bridge sp-local-bridge-mcp sp-local-bridge-doctor sp-local-bridge-print-config)

    # First check all expected executables exist in the bin dir
    for cmd in "${commands[@]}"; do
        if [[ -x "$bin_dir/$cmd" ]]; then
            info "✓ $cmd → $bin_dir/$cmd"
        else
            error "$cmd not found at $bin_dir/$cmd after install"
            INSTALL_OK=false
        fi
    done

    # Then check if the bin dir is on PATH
    if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
        echo
        warn "Install directory is NOT on your PATH: $bin_dir"
        warn "MCP hosts launched from a GUI may also not see these commands."
        echo
        echo "  Fix: add to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        echo "    export PATH=\"$bin_dir:\$PATH\""
        echo
        echo "  Or use absolute paths in host config (the default):"
        echo "    $bin_dir/sp-local-bridge-print-config claude-desktop"
        echo
        INSTALL_OK=false
    fi

    # Behavioral assertion: verify installed code is current (not stale cache)
    local config_cmd="$bin_dir/sp-local-bridge-print-config"
    if [[ -x "$config_cmd" ]]; then
        local help_out
        help_out=$("$config_cmd" --help 2>&1 || true)
        if [[ "$help_out" != *"--bare"* ]]; then
            error "Installed sp-local-bridge-print-config is stale (missing --bare flag)."
            error "Try: uv tool install --reinstall --from '$SCRIPT_DIR' sp-local-bridge"
            INSTALL_OK=false
        else
            info "✓ installed code is current (behavioral check passed)"
        fi
    fi
}

print_next_steps() {
    local bin_dir
    bin_dir=$(resolve_tool_bin_dir)
    local mcp_cmd="sp-local-bridge-mcp"
    local doctor_cmd="sp-local-bridge-doctor"
    local config_cmd="sp-local-bridge-print-config"

    # Use absolute paths if not on PATH
    if ! command -v sp-local-bridge-mcp &>/dev/null && [[ -x "$bin_dir/sp-local-bridge-mcp" ]]; then
        mcp_cmd="$bin_dir/sp-local-bridge-mcp"
        doctor_cmd="$bin_dir/sp-local-bridge-doctor"
        config_cmd="$bin_dir/sp-local-bridge-print-config"
    fi

    echo
    echo "Next steps:"
    echo "  1. Enable Local REST API in Super Productivity: Settings → Misc"
    echo "  2. Run: $doctor_cmd"
    echo "  3. For MCP host config: $config_cmd claude-desktop"
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

    if [[ "$INSTALL_OK" != "true" ]]; then
        error "Install completed but commands are not accessible on PATH."
        error "Fix PATH (see above) and re-run, or use absolute paths."
        exit 1
    fi
}

main "$@"
