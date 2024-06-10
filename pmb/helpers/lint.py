# Copyright 2023 Danct12 <danct12@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from typing import Dict, List, Sequence
from pmb.core.chroot import Chroot
from pmb.core.pkgrepo import pkgrepo_iter_package_dirs, pkgrepo_names, pkgrepo_relative_path
from pmb.helpers import logging
import os

import pmb.chroot
import pmb.chroot.apk
import pmb.build
from pmb.types import PmbArgs
import pmb.helpers.run
import pmb.helpers.pmaports


def check(pkgnames: Sequence[str]):
    """Run apkbuild-lint on the supplied packages.

    :param pkgnames: Names of the packages to lint
    """
    chroot = Chroot.native()
    pmb.chroot.init(chroot)
    pmb.chroot.apk.install(["atools"], chroot)

    # Mount pmaports.git inside the chroot so that we don't have to copy the
    # package folders
    dest_paths = pmb.build.mount_pmaports(chroot)

    # Locate all APKBUILDs and make the paths be relative to the pmaports
    # root
    apkbuilds: Dict[str, List[str]] = dict(map(lambda x: (x, []), pkgrepo_names()))
    found_pkgnames = set()
    # If a package exists in multiple aports we will lint all of them
    # since.. well, what else do we do?
    for pkgdir in pkgrepo_iter_package_dirs():
        if pkgdir.name not in pkgnames:
            continue

        repo, relpath = pkgrepo_relative_path(pkgdir)
        apkbuilds[repo.name].append(os.fspath(relpath / "APKBUILD"))
        found_pkgnames.add(pkgdir.name)

    # Check we found all the packages in pkgnames
    if len(found_pkgnames) != len(pkgnames):
        missing = set(pkgnames) - found_pkgnames
        logging.error(f"Could not find the following packages: {missing}")
        return

    # Run apkbuild-lint in chroot from the pmaports mount point. This will
    # print a nice source identifier à la "./cross/grub-x86/APKBUILD" for
    # each violation.
    pkgstr = ", ".join(pkgnames)
    logging.info(f"(native) linting {pkgstr} with apkbuild-lint")
    options = pmb.config.apkbuild_custom_valid_options

    # For each pkgrepo run the linter on the relevant packages
    for repo, apkbuild_paths in apkbuilds.items():
        pmb.chroot.root(["apkbuild-lint"] + apkbuild_paths,
                        check=False, output="stdout",
                        output_return=True,
                        working_dir=dest_paths[repo],
                        env={"CUSTOM_VALID_OPTIONS": " ".join(options)})
