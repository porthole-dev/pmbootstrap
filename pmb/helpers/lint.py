# Copyright 2023 Danct12 <danct12@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import Sequence
from pmb.core.chroot import Chroot
from pmb.core.pkgrepo import pkgrepo_iter_package_dirs, pkgrepo_names, pkgrepo_relative_path
from pmb.helpers import logging
from pmb.helpers.exceptions import NonBugError
import os

import pmb.chroot
import pmb.chroot.apk
import pmb.build
import pmb.helpers.run
import pmb.helpers.pmaports


# FIXME: dest_paths[repo], repo expected to be a Literal.
# We should really make Config.mirrors not a TypedDict.
# mypy: disable-error-code="index"
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
    apkbuilds: dict[str, list[str]] = dict(map(lambda x: (x, []), pkgrepo_names()))
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

    # apkbuild-lint output is not colorized, make it easier to spot
    logging.info("*** apkbuild-lint output ***")

    # For each pkgrepo run the linter on the relevant packages
    has_failed = False
    for pkgrepo, apkbuild_paths in apkbuilds.items():
        if pmb.chroot.user(
            ["apkbuild-lint"] + apkbuild_paths,
            check=False,
            output="stdout",
            working_dir=dest_paths[repo.name],
            env={"CUSTOM_VALID_OPTIONS": " ".join(options)},
        ):
            has_failed = True

    logging.info("*** apkbuild-lint output ***")

    if has_failed:
        raise NonBugError("Linter failed!")
