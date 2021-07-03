#!/bin/sh -e
# Install pmbootstrap depends, set up pmos user with sudo
if [ "$(id -u)" != 0 ]; then
	echo "ERROR: this script is meant to be executed in the gitlab-ci"
	echo "environment only."
	exit 1
fi

topdir="$(realpath "$(dirname "$0")/..")"
cd "$topdir"

ln -sf "$PWD"/pmbootstrap.py /usr/local/bin/pmbootstrap

apk add -q \
	git \
	openssl \
	py3-pytest \
	py3-pytest-cov \
	sudo

adduser -D pmos
chown -R pmos:pmos .
echo 'pmos ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

su pmos -c "git config --global user.email postmarketos-ci@localhost"
su pmos -c "git config --global user.name postmarketOS_CI"

echo "Initializing pmbootstrap"
if ! su pmos -c "yes '' | pmbootstrap \
		--details-to-stdout \
		init \
		>/tmp/pmb_init 2>&1"; then
	cat /tmp/pmb_init
	exit 1
fi
echo ""
