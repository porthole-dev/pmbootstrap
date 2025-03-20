#!/bin/sh -e
# Description: lint all python scripts
# https://postmarketos.org/pmb-ci

if [ "$(id -u)" = 0 ]; then
	set -x
	apk -q add py3-pip
	# pin to ruff 0.11.0 until this is fixed:
	# https://github.com/astral-sh/ruff/issues/16874
	pip install --break-system-packages --no-warn-script-location ruff==0.11.0
	exec su "${TESTUSER:-build}" -c "sh -e $0"
fi

DID_FAIL=0

set -x

# Lint all files
ruff check || DID_FAIL=1

# Check formatting
ruff format --diff || DID_FAIL=1

exit $DID_FAIL
