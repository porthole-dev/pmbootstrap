#!/bin/sh -e
# Description: lint all markdown files
# https://postmarketos.org/pmb-ci

if [ "$(id -u)" = 0 ]; then
	set -x
	apk add npm
	npm install -g markdownlint-cli
	ln -sf /usr/local/lib/node_modules/markdownlint-cli/markdownlint.js /usr/bin/markdownlint-cli
	exec su "${TESTUSER:-build}" -c "sh -e $0"
fi

MDL_FAILED=0
find . -name '*.md' |
while read -r file; do
	echo "mdl: $file"
	markdownlint-cli "$file" || MDL_FAILED=1
done

if [ "$MDL_FAILED" = "1" ]; then
	echo "markdown lint failed!"
	exit 1
fi
