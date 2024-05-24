# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import Generator, List, Optional
from pathlib import Path, PosixPath, PurePosixPath
from pmb import commands
from pmb.core.types import PathString
from pmb.helpers import run
from pmb.core import get_context
from pmb import config

class Log(commands.Command):
    clear_log: bool
    lines: int
    
    def __init__(self, clear_log: bool, lines: int):
        self.clear_log = clear_log
        self.lines = lines

    def run(self):
        context = get_context()
        log_testsuite = config.work / "log_testsuite.txt"

        if self.clear_log:
            run.user(["truncate", "-s", "0", context.log])
            run.user(["truncate", "-s", "0", log_testsuite])

        cmd: List[PathString] = ["tail", "-n", str(self.lines), "-F"]

        # Follow the testsuite's log file too if it exists. It will be created when
        # starting a test case that writes to it (git -C test grep log_testsuite).
        if log_testsuite.exists():
            cmd += [log_testsuite]

        # tail writes the last lines of the files to the terminal. Put the regular
        # log at the end, so that output is visible at the bottom (where the user
        # looks for an error / what's currently going on).
        cmd += [context.log]

        run.user(cmd, output="tui")

