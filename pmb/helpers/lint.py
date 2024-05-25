# Copyright 2023 Danct12 <danct12@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from pmb.helpers import logging
import os

import pmb.chroot
import pmb.chroot.apk
import pmb.build
from pmb.types import PmbArgs
import pmb.helpers.run
import pmb.helpers.pmaports


def check(args: PmbArgs, pkgnames):
    """Run apkbuild-lint on the supplied packages.

    :param pkgnames: Names of the packages to lint
    """
    pmb.chroot.apk.install(["atools"])

    # Mount pmaports.git inside the chroot so that we don't have to copy the
    # package folders
    pmaports = Path("/mnt/pmaports")
    pmb.build.mount_pmaports(args, pmaports)

    # Locate all APKBUILDs and make the paths be relative to the pmaports
    # root
    apkbuilds = []
    for pkgname in pkgnames:
        aport = pmb.helpers.pmaports.find(pkgname)
        if not (aport / "APKBUILD").exists():
            raise ValueError(f"Path does not contain an APKBUILD file: {aport}")
        relpath = os.path.relpath(aport, args.aports)
        apkbuilds.append(f"{relpath}/APKBUILD")

    # Run apkbuild-lint in chroot from the pmaports mount point. This will
    # print a nice source identifier à la "./cross/grub-x86/APKBUILD" for
    # each violation.
    pkgstr = ", ".join(pkgnames)
    logging.info(f"(native) linting {pkgstr} with apkbuild-lint")
    options = pmb.config.apkbuild_custom_valid_options
    return pmb.chroot.root(["apkbuild-lint"] + apkbuilds,
                           check=False, output="stdout",
                           output_return=True,
                           working_dir=pmaports,
                           env={"CUSTOM_VALID_OPTIONS": " ".join(options)})
