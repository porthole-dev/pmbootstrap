#!/bin/sh -e
# Description: lint all python scripts
# https://postmarketos.org/pmb-ci

if [ "$(id -u)" = 0 ]; then
	set -x
	apk -q add py3-pip
	pip install --break-system-packages --no-warn-script-location ruff==0.13.2
	exec su "${TESTUSER:-build}" -c "sh -e $0"
fi

DID_FAIL=0

set -x

# Lint all files
ruff check || DID_FAIL=1

# Check formatting
ruff format --diff || DID_FAIL=1

exit $DID_FAIL
