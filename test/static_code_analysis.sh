#!/bin/sh
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
set -e
DIR="$(cd "$(dirname "$0")" && pwd -P)"
cd "$DIR/.."

# Make sure that the work folder format is up to date, and that there are no
# mounts from aborted test cases (#1595)
./pmbootstrap.py work_migrate
./pmbootstrap.py -q shutdown

# Install needed packages
echo "Initializing Alpine chroot (details: 'pmbootstrap log')"
./pmbootstrap.py -q chroot -- apk -q add \
	shellcheck \
	python3 \
	py3-flake8 || return 1

rootfs_native="$(./pmbootstrap.py config work)/chroot_native"
command="$rootfs_native/lib/ld-musl-$(uname -m).so.1"
command="$command --library-path=$rootfs_native/lib:$rootfs_native/usr/lib"
shellcheck_command="$command $rootfs_native/usr/bin/shellcheck"
flake8_command="$command $rootfs_native/usr/bin/python3 $rootfs_native/usr/bin/flake8"

# Shell: shellcheck
find . -name '*.sh' |
while read -r file; do
	echo "Test with shellcheck: $file"
	cd "$DIR/../$(dirname "$file")"
	$shellcheck_command -e SC1008 -x "$(basename "$file")"
done

# Python: flake8
# E501: max line length
# F401: imported, but not used, does not make sense in __init__ files
# E402: module import not on top of file, not possible for testcases
# E722: do not use bare except
cd "$DIR"/..
echo "Test with flake8: *.py"
# Note: omitting a virtualenv if it is here (e.g. gitlab CI)
py_files="$(find . -not -path '*/venv/*' -name '*.py')"
_ignores="E501,E402,E722,W504,W605"
# shellcheck disable=SC2086
$flake8_command --exclude=__init__.py --ignore "$_ignores" $py_files
# shellcheck disable=SC2086
$flake8_command --filename=__init__.py --ignore "F401,$_ignores" $py_files

# Enforce max line length of 79 characters (#1986). We are iteratively fixing
# up the source files to adhere to this rule, so only check the ones that were
# fixed for now. Eventually, E501 can be removed from _ignores above, and this
# whole block can be removed.
echo "Test with flake8: *.py (E501)"
py_files="
	.gitlab/check_mr_settings.py
	pmb/aportgen/device.py
	pmb/build/__init__.py
	pmb/build/autodetect.py
	pmb/build/checksum.py
	pmb/build/menuconfig.py
	pmb/build/newapkbuild.py
	pmb/chroot/__init__.py
	pmb/chroot/apk.py
	pmb/chroot/apk_static.py
	pmb/chroot/binfmt.py
	pmb/chroot/distccd.py
	pmb/chroot/init.py
	pmb/chroot/initfs.py
	pmb/chroot/initfs_hooks.py
	pmb/chroot/mount.py
	pmb/chroot/other.py
	pmb/chroot/root.py
	pmb/chroot/shutdown.py
	pmb/chroot/user.py
	pmb/chroot/zap.py
	pmb/config/pmaports.py
	pmb/config/save.py
	pmb/config/workdir.py
	pmb/export/__init__.py
	pmb/export/frontend.py
	pmb/export/symlinks.py
	pmb/flasher/__init__.py
	pmb/helpers/__init__.py
	pmb/helpers/apk.py
	pmb/helpers/aportupgrade.py
	pmb/helpers/args.py
	pmb/helpers/file.py
	pmb/helpers/git.py
	pmb/helpers/lint.py
	pmb/helpers/mount.py
	pmb/helpers/package.py
	pmb/helpers/repo.py
	pmb/helpers/repo_missing.py
	pmb/helpers/run.py
	pmb/helpers/status.py
	pmb/helpers/ui.py
	pmb/install/__init__.py
	pmb/install/_install.py
	pmb/install/blockdevice.py
	pmb/install/format.py
	pmb/install/losetup.py
	pmb/install/partition.py
	pmb/install/recovery.py
	pmb/install/ui.py
	pmb/parse/__init__.py
	pmb/parse/_apkbuild.py
	pmb/parse/apkindex.py
	pmb/parse/arch.py
	pmb/parse/arguments.py
	pmb/parse/binfmt_info.py
	pmb/parse/bootimg.py
	pmb/parse/cpuinfo.py
	pmb/parse/depends.py
	pmb/parse/deviceinfo.py
	pmb/parse/kconfig.py
	pmb/parse/version.py
	pmb/qemu/__init__.py
	pmb/sideload/__init__.py
	pmbootstrap.py
	test/pmb_test/__init__.py
	test/pmb_test/const.py
	test/pmb_test/git.py
	test/test_aportgen.py
	test/test_bootimg.py
	test/test_config_init.py
	test/test_config_pmaports.py
	test/test_config_workdir.py
	test/test_cross_compile_distcc.py
	test/test_crossdirect.py
	test/test_envkernel.py
	test/test_file.py
	test/test_folder_size.py
	test/test_frontend.py
	test/test_helpers_git.py
	test/test_helpers_lint.py
	test/test_helpers_package.py
	test/test_helpers_pmaports.py
	test/test_helpers_repo.py
	test/test_helpers_repo_missing.py
	test/test_helpers_status.py
	test/test_helpers_ui.py
	test/test_install.py
	test/test_kconfig_check.py
	test/test_keys.py
	test/test_mount.py
	test/test_newapkbuild.py
	test/test_parse_apkbuild.py
	test/test_parse_apkindex.py
	test/test_parse_depends.py
	test/test_parse_deviceinfo.py
	test/test_questions.py
	test/test_run_core.py
	test/test_shell_escape.py
	test/test_version.py
	test/test_version_validate.py
"
# shellcheck disable=SC2086
$flake8_command --select="E501" $py_files

# Done
echo "Success!"
