# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pmb.helpers import logging
from pathlib import Path
import pmb.chroot.run
from pmb.core.types import PmbArgs
import pmb.helpers.cli
import pmb.parse
import pmb.build

from pmb.core import Chroot


def newapkbuild(args: PmbArgs, folder, args_passed, force=False):
    # Initialize build environment and build folder
    pmb.build.init(args)
    build = Path("/home/pmos/build")
    build_outside = Chroot.native() / build
    if build_outside.exists():
        pmb.chroot.root(args, ["rm", "-r", build])
    pmb.chroot.user(args, ["mkdir", "-p", build])

    # Run newapkbuild
    pmb.chroot.user(args, ["newapkbuild"] + args_passed, working_dir=build)
    glob_result = list(build_outside.glob("/*/APKBUILD"))
    if not len(glob_result):
        return

    # Paths for copying
    source_apkbuild = glob_result[0]
    pkgname = pmb.parse.apkbuild(source_apkbuild, False)["pkgname"]
    target = args.aports / folder / pkgname

    # Move /home/pmos/build/$pkgname/* to /home/pmos/build/*
    for path in build_outside.glob("/*/*"):
        path_inside = build / pkgname / os.path.basename(path)
        pmb.chroot.user(args, ["mv", path_inside, build])
    pmb.chroot.user(args, ["rmdir", build / pkgname])

    # Overwrite confirmation
    if os.path.exists(target):
        logging.warning("WARNING: Folder already exists: " + target)
        question = "Continue and delete its contents?"
        if not force and not pmb.helpers.cli.confirm(args, question):
            raise RuntimeError("Aborted.")
        pmb.helpers.run.user(args, ["rm", "-r", target])

    # Copy the aport (without the extracted src folder)
    logging.info("Create " + target)
    pmb.helpers.run.user(args, ["mkdir", "-p", target])
    for path in build_outside.glob("/*"):
        if not path.is_dir():
            pmb.helpers.run.user(args, ["cp", path, target])
