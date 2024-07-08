# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from pmb import commands
from pmb.core.context import get_context
import pmb.parse.kconfig
import pmb.helpers.git
import pmb.config
import logging


class KConfigCheck(commands.Command):
    details: bool
    file: str
    packages: list[str]

    def __init__(self, details, file, packages):
        self.details = details
        self.file = file
        self.packages = packages

    def run(self):
        # Build the components list from cli arguments (--waydroid etc.)
        components_list: list[str] = []

        # Handle passing a file directly
        if self.file:
            if pmb.parse.kconfig.check_file(self.file, components_list, details=self.details):
                logging.info("kconfig check succeeded!")
                return
            raise RuntimeError("kconfig check failed!")

        # Default to all kernel packages
        if not self.packages:
            for pkg in pmb.helpers.pmaports.get_list():
                if pkg.startswith("linux-"):
                    self.packages.append(pkg.split("linux-")[1])

        # Iterate over all kernels
        error = False
        skipped = 0
        self.packages.sort()
        for package in self.packages:
            if not get_context().force:
                pkgname = package if package.startswith("linux-") else f"linux-{package}"
                aport = pmb.helpers.pmaports.find(pkgname)
                apkbuild = pmb.parse.apkbuild(aport)
                if "!pmb:kconfigcheck" in apkbuild["options"]:
                    skipped += 1
                    continue
            if not pmb.parse.kconfig.check(package, components_list, details=self.details):
                error = True

        # At least one failure
        if error:
            raise RuntimeError("kconfig check failed!")
        else:
            if skipped:
                logging.info(
                    f"NOTE: {skipped} kernel{' was' if skipped == 1 else 's were'} skipped"
                    " (consider 'pmbootstrap kconfig check -f')"
                )
            logging.info("kconfig check succeeded!")
