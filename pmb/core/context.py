# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

"""Global runtime context"""

import pmb.config
from pathlib import Path


class Context():
    details_to_stdout: bool
    quiet: bool
    command_timeout: float
    sudo_timer: bool
    log: Path

    def __init__(self):
        self.details_to_stdout = False
        self.command_timeout = 0
        self.sudo_timer = False
        self.log = pmb.config.work / "log.txt"
        self.quiet = False
