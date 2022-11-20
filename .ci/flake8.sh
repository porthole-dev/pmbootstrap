#!/bin/sh -e
# Description: lint all python scripts
# https://postmarketos.org/pmb-ci

if [ "$(id -u)" = 0 ]; then
	set -x
	apk -q add py3-flake8
	exec su "${TESTUSER:-build}" -c "sh -e $0"
fi

# E402: module import not on top of file, not possible for testcases
# E722: do not use bare except
# W504: line break occurred after a binary operator
ign="E402,E722,W504"

set -x

# __init__.py with additional ignore:
# F401: imported, but not used
# shellcheck disable=SC2046
flake8 --ignore "F401,$ign" $(find . -not -path '*/venv/*' -name '__init__.py')

# Check all other files
flake8 --ignore="$ign" --exclude=__init__.py
