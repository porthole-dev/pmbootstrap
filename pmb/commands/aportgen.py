# Copyright 2024 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import pmb.aportgen
from pmb import commands
from pmb.helpers import logging


class Aportgen(commands.Command):
    def __init__(
        self, package_list: list[str], fork_alpine: bool, fork_alpine_retain_branch: bool
    ) -> None:
        self.package_list = package_list
        self.fork_alpine = fork_alpine
        self.fork_alpine_retain_branch = fork_alpine_retain_branch

    def run(self) -> None:
        for package in self.package_list:
            logging.info(f"Generate aport: {package}")
            pmb.aportgen.generate(package, self.fork_alpine, self.fork_alpine_retain_branch)
