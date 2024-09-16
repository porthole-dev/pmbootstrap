#!/bin/sh -e
# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" != "CALLED_FROM_PMB" ]; then
	echo "ERROR: this script is only meant to be called by pmbootstrap"
	exit 1
fi

CHROOT="$2"

test -n "$CHROOT"
test -f "$CHROOT"/in-pmbootstrap

if [ -L "$CHROOT"/bin ]; then
	echo "ERROR: chroot has merged usr already: $CHROOT"
	exit 1
fi

merge() {
	local src="$1"
	local dest="$2"

	mv "$CHROOT/$src/"* "$CHROOT/$dest/"
	rmdir "$CHROOT/$src"
	ln -s "/$dest" "$CHROOT/$src"
}

merge bin usr/bin
merge sbin usr/bin
merge lib usr/lib
merge usr/sbin usr/bin
