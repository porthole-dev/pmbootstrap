# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pmb.chroot
from pmb import commands


class Shutdown(commands.Command):
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        pmb.chroot.shutdown()
