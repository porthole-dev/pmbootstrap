#!/bin/sh -e
topdir="$(realpath "$(dirname "$0")/..")"
cd "$topdir"

# Make sure that the work folder format is up to date, and that there are no
# mounts from aborted test cases (#1595)
./pmbootstrap.py work_migrate
./pmbootstrap.py -q shutdown

# Make sure we have a valid device (#1128)
device="$(./pmbootstrap.py config device)"
pmaports="$(./pmbootstrap.py config aports)"
deviceinfo="$(ls -1 "$pmaports"/device/*/device-"$device"/deviceinfo)"
if ! [ -e "$deviceinfo" ]; then
	echo "ERROR: Could not find deviceinfo file for selected device:" \
		"$device"
	echo "Expected path: $deviceinfo"
	echo "Maybe you have switched to a branch where your device does not"
	echo "exist? Use 'pmbootstrap config device qemu-amd64' to switch to"
	echo "a valid device."
	exit 1
fi

pytest -vv -x --cov=pmb test -m "not skip_ci" "$@"
