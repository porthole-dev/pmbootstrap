# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
from pathlib import Path

import pmb.chroot
import pmb.build
from pmb.core.types import PmbArgs
import pmb.helpers.run
import pmb.helpers.pmaports
from pmb.core import Chroot


def update(args: PmbArgs, pkgname):
    """Fetch all sources and update the checksums in the APKBUILD."""
    pmb.build.init_abuild_minimal(args)
    pmb.build.copy_to_buildpath(args, pkgname)
    logging.info("(native) generate checksums for " + pkgname)
    pmb.chroot.user(args, ["abuild", "checksum"],
                    working_dir=Path("/home/pmos/build"))

    # Copy modified APKBUILD back
    source = Chroot.native() / "home/pmos/build/APKBUILD"
    target = f"{os.fspath(pmb.helpers.pmaports.find(args, pkgname))}/"
    pmb.helpers.run.user(args, ["cp", source, target])


def verify(args: PmbArgs, pkgname):
    """Fetch all sources and verify their checksums."""
    pmb.build.init_abuild_minimal(args)
    pmb.build.copy_to_buildpath(args, pkgname)
    logging.info("(native) verify checksums for " + pkgname)

    # Fetch and verify sources, "fetch" alone does not verify them:
    # https://github.com/alpinelinux/abuild/pull/86
    pmb.chroot.user(args, ["abuild", "fetch", "verify"],
                    working_dir=Path("/home/pmos/build"))
