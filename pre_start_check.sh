#!/bin/bash
# Pre-start validation for trive_aquasense.service
# Checks prerequisites before the service starts to prevent silent failures.

set -euo pipefail

INSTALL_DIR="/opt/trive_aquasense"
CONFIG_FILE="/etc/trive_aquasense/config.json"
VENV_PYTHON="${INSTALL_DIR}/venv/bin/python"

fail() {
    echo "ERROR: $1" >&2
    exit 1
}

# Check venv exists and is executable
[ -x "${VENV_PYTHON}" ] || fail "Virtual environment not found at ${VENV_PYTHON}. Run the install script first."

# Check config.json is present and readable
[ -f "${CONFIG_FILE}" ] || fail "config.json not found at ${CONFIG_FILE}."
[ -r "${CONFIG_FILE}" ] || fail "config.json at ${CONFIG_FILE} is not readable by this user."

# Check required environment variables are set (injected by EnvironmentFile)
[ -n "${ACCESS_TOKEN:-}" ]        || fail "Required env var ACCESS_TOKEN is not set in /etc/trive_aquasense/.env."
[ -n "${THINGSBOARD_SERVER:-}" ]  || fail "Required env var THINGSBOARD_SERVER is not set in /etc/trive_aquasense/.env."

echo "Pre-start checks passed."