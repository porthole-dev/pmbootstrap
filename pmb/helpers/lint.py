# Copyright 2021 Danct12 <danct12@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import pmb.chroot
import pmb.chroot.apk
import pmb.build
import pmb.helpers.run
import pmb.helpers.pmaports


def check(args, pkgname):
    pmb.chroot.apk.install(args, ["atools"])

    # Run apkbuild-lint on copy of pmaport in chroot
    pmb.build.init(args)
    pmb.build.copy_to_buildpath(args, pkgname)
    logging.info("(native) linting " + pkgname + " with apkbuild-lint")
    options = pmb.config.apkbuild_custom_valid_options
    return pmb.chroot.user(args, ["apkbuild-lint", "APKBUILD"],
                           check=False, output="stdout",
                           output_return=True,
                           working_dir="/home/pmos/build",
                           env={"CUSTOM_VALID_OPTIONS": " ".join(options)})
