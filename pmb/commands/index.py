# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pmb.build.other
from pmb import commands


class Index(commands.Command):
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        pmb.build.other.index_repo()
