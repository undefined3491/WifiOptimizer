#!/bin/bash
# WiFi Optimizer TMS - Decky Plugin rescue/bootstrap installer.
#
# Rescue-only discipline: sibling staging under the plugin base with a
# same-filesystem gate, validated transfer/identity, and per-file atomic
# renames. The live directory is never removed (no `rm -rf` of live);
# `rm -rf` touches only the stage dir. Reports FILE_COMMIT/RESTART_RC/
# NEXT_HEALTH truthfully and exits non-zero on any failure.

set -e

# Compatibility directory key; the public name comes from plugin.json.
PLUGIN_NAME="WiFi Optimizer"
PLUGIN_DISPLAY_NAME="WiFi Optimizer TMS"

# Shipped payload allowlist (mirrors the in-app updater contract).
SHIPPED_FILES="plugin.json package.json main.py decky.pyi dist/index.js dist/index.js.map defaults/dispatcher.sh.tmpl"

# Check for root (needed to write to plugin dir and restart service)
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run with sudo."
    echo "Run: sudo bash $0"
    exit 1
fi

# Resolve the real user's home directory (same method as Decky's own installer)
DECK_USER="${SUDO_USER:-$(logname 2>/dev/null || echo deck)}"
USER_HOME="$(getent passwd "$DECK_USER" | cut -d: -f6)"
if [ -z "$USER_HOME" ]; then
    USER_HOME="/home/$DECK_USER"
fi

PLUGIN_BASE="$USER_HOME/homebrew/plugins"
PLUGIN_DIR="$PLUGIN_BASE/$PLUGIN_NAME"

# Check Decky is installed
if [ ! -d "$PLUGIN_BASE" ]; then
    echo "Error: Decky Loader not found at $PLUGIN_BASE"
    echo "Install it first: https://decky.xyz"
    exit 1
fi

fail() {
    echo "Error: $1"
    echo "FILE_COMMIT=\"$COMMITTED/7\""
    echo 'RESTART_RC="not_attempted"'
    echo 'NEXT_HEALTH="unknown"'
    exit 1
}

COMMITTED=0

# Fetch latest release tag from GitHub (validated transfer)
echo "Checking for latest release..."
LATEST_TAG="$(curl -fsSL --proto =https --connect-timeout 5 --max-time 30 --fail "https://api.github.com/repos/undefined3491/wifi-optimizer-tms/releases/latest" 2>/dev/null | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')" || LATEST_TAG=""

FALLBACK_LABEL=""
if [ -z "$LATEST_TAG" ]; then
    echo "Warning: Couldn't fetch latest release; UNRELEASED-FALLBACK to main branch"
    FALLBACK_LABEL="UNRELEASED-FALLBACK "
    REPO_URL="https://github.com/undefined3491/wifi-optimizer-tms/archive/refs/heads/main.tar.gz"
    DIR_NAME="wifi-optimizer-tms-main"
    EXPECTED_VERSION=""
else
    echo "Latest release: $LATEST_TAG"
    REPO_URL="https://github.com/undefined3491/wifi-optimizer-tms/archive/refs/tags/${LATEST_TAG}.tar.gz"
    DIR_NAME="wifi-optimizer-tms-${LATEST_TAG#v}"
    EXPECTED_VERSION="${LATEST_TAG#v}"
fi

# Sibling staging under the plugin base (same filesystem by construction,
# never bare /tmp which may live on a different filesystem and degrade
# rename to copy). Private name, 0700.
STAGE_DIR="$(mktemp -d "$PLUGIN_BASE/.wifi-otp-stage.XXXXXX")"
chmod 700 "$STAGE_DIR"

cleanup() {
    rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

# Same-filesystem gate: the stage must live on the live dir's filesystem,
# otherwise per-file renames are not atomic.
BASE_DEV="$(stat -c %d "$PLUGIN_BASE")"
STAGE_DEV="$(stat -c %d "$STAGE_DIR")"
if [ "$BASE_DEV" != "$STAGE_DEV" ]; then
    fail "stage is not on the plugin filesystem (dev $STAGE_DEV != $BASE_DEV)"
fi

echo "Installing ${FALLBACK_LABEL}$PLUGIN_DISPLAY_NAME..."

# Download and extract (validated transfer)
echo "Downloading..."
if ! curl -fsSL --proto =https --connect-timeout 5 --max-time 120 --fail "$REPO_URL" -o "$STAGE_DIR/plugin.tar.gz"; then
    fail "download failed for $REPO_URL"
fi
mkdir -p "$STAGE_DIR/extract"
if ! tar xzf "$STAGE_DIR/plugin.tar.gz" -C "$STAGE_DIR/extract"; then
    fail "archive is corrupt or unreadable"
fi

SRC="$STAGE_DIR/extract/$DIR_NAME"
if [ ! -f "$SRC/plugin.json" ]; then
    fail "download failed or repo structure changed (no $DIR_NAME/plugin.json)"
fi

# Identity checks before the first live write: single expected root is
# implied by $SRC; every shipped file must exist; manifests must name this
# plugin; the version must match the release tag (or be a plain version on
# the labeled main fallback); both dist files must be non-empty.
for required in $SHIPPED_FILES; do
    if [ ! -f "$SRC/$required" ]; then
        fail "archive is missing shipped file: $required"
    fi
done
if ! grep -q '"name": "WiFi Optimizer TMS"' "$SRC/plugin.json"; then
    fail "plugin.json identity mismatch (name)"
fi
if ! grep -q '"name": "wifi-optimizer-tms"' "$SRC/package.json"; then
    fail "package.json identity mismatch (name)"
fi
if [ -n "$EXPECTED_VERSION" ]; then
    if ! grep -q "\"version\": \"$EXPECTED_VERSION\"" "$SRC/package.json"; then
        fail "package.json identity mismatch (version is not $EXPECTED_VERSION)"
    fi
else
    if ! grep -Eq '"version": "[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?"' "$SRC/package.json"; then
        fail "package.json identity mismatch (no plain version on main fallback)"
    fi
fi
if [ ! -s "$SRC/dist/index.js" ] || [ ! -s "$SRC/dist/index.js.map" ]; then
    fail "dist payload is empty"
fi

# Commit. The live directory is never removed or renamed: both fresh and
# upgrade commit only the 7 allowlisted files via per-file renames (atomic
# on the same filesystem), never truncating cp and never moving the whole
# tree. The live dir is re-checked atomically directly before commit
# (TOCTOU): mkdir succeeds only when live is still absent; otherwise the
# upgrade path is taken instead of nesting the tree inside live.
if [ ! -d "$PLUGIN_DIR" ]; then
    echo "Installing to $PLUGIN_DIR..."
    UPGRADING=false
    # Atomic fresh gate: succeeds only when live is still absent at commit
    # time. Fresh uses no-clobber per-file moves (mv -n); the fallback
    # below uses plain overwriting moves.
    if mkdir "$PLUGIN_DIR" 2>/dev/null; then
        mkdir -p "$PLUGIN_DIR/dist" "$PLUGIN_DIR/defaults" "$PLUGIN_DIR/py_modules"
        for shipped in $SHIPPED_FILES; do
            if mv -n "$SRC/$shipped" "$PLUGIN_DIR/$shipped"; then
                COMMITTED=$((COMMITTED + 1))
            else
                # Mid-loop failure: withhold the restart, report the partial
                # count, and retain the stage for retry (drop the EXIT trap).
                trap - EXIT
                fail "commit failed at $shipped (stage retained for retry: $STAGE_DIR)"
            fi
        done
        touch "$PLUGIN_DIR/py_modules/.keep"
    else
        echo "Live directory appeared during install; upgrading existing installation..."
        UPGRADING=true
        mkdir -p "$PLUGIN_DIR/dist" "$PLUGIN_DIR/defaults"
        for shipped in $SHIPPED_FILES; do
            if mv "$SRC/$shipped" "$PLUGIN_DIR/$shipped"; then
                COMMITTED=$((COMMITTED + 1))
            else
                # Mid-loop failure: withhold the restart, report the partial
                # count, and retain the stage for retry (drop the EXIT trap).
                trap - EXIT
                fail "commit failed at $shipped (stage retained for retry: $STAGE_DIR)"
            fi
        done
        mkdir -p "$PLUGIN_DIR/py_modules"
        touch "$PLUGIN_DIR/py_modules/.keep"
    fi
else
    echo "Upgrading existing installation..."
    UPGRADING=true
    mkdir -p "$PLUGIN_DIR/dist" "$PLUGIN_DIR/defaults"
    for shipped in $SHIPPED_FILES; do
        if mv "$SRC/$shipped" "$PLUGIN_DIR/$shipped"; then
            COMMITTED=$((COMMITTED + 1))
        else
            # Mid-loop failure: withhold the restart, report the partial
            # count, and retain the stage for retry (drop the EXIT trap).
            trap - EXIT
            fail "commit failed at $shipped (stage retained for retry: $STAGE_DIR)"
        fi
    done
    mkdir -p "$PLUGIN_DIR/py_modules"
    touch "$PLUGIN_DIR/py_modules/.keep"
fi

# Restart Decky (exactly one request after a successful commit)
echo "Restarting Decky Loader..."
RESTART_RC=0
if systemctl restart plugin_loader 2>/dev/null; then
    RESTART_RC=0
else
    RESTART_RC="$?"
fi

echo ""
if [ "$UPGRADING" = true ]; then
    echo "$PLUGIN_DISPLAY_NAME updated! Your settings have been preserved."
else
    echo "$PLUGIN_DISPLAY_NAME installed! Open the Quick Access Menu to configure."
fi
echo "FILE_COMMIT=\"$COMMITTED/7\""
echo "RESTART_RC=\"$RESTART_RC\""
echo 'NEXT_HEALTH="load_unconfirmed (verify version after restart)"'

if [ "$RESTART_RC" != "0" ]; then
    echo "Error: plugin_loader restart failed (rc=$RESTART_RC)"
    exit 1
fi
