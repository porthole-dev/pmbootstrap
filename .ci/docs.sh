#!/bin/sh -e
# Description: create documentation with sphinx
# Options: native
# https://postmarketos.org/pmb-ci


# Ensure sphinx_rtd_theme is installed
if [ "$(id -u)" = 0 ]; then
	set -x
	apk -q add \
		py3-sphinx_rtd_theme \
		py3-sphinxcontrib-autoprogram
	exec su "${TESTUSER:-build}" -c "sh -e $0"
fi

# Require sphinx to be installed on the host system
if [ -z "$(command -v sphinx-build)" ]; then
	echo "ERROR: sphinx-build command not found, make sure it is in your PATH."
	exit 1
fi

sphinx-build \
	docs \
	public \

#	-E -a -v -T
