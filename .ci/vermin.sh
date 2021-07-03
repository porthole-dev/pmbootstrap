#!/bin/sh -e
_vermin() {
	if ! vermin -q "$@" >/dev/null 2>&1; then
		vermin -vv "$@"
	fi
}

# shellcheck disable=SC2046
_vermin \
	-t=3.6- \
	--backport argparse \
	--backport configparser \
	--backport enum \
	--backport typing \
	$(find . -name '*.py' \
		-a -not -path "./.venv/*" \
		-a -not -path "./venv/*")

echo "vermin check passed"
