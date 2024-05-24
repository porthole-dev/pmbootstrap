# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

"""Global runtime context"""

class Context():
    details_to_stdout: bool
    quiet: bool
    command_timeout: float
    sudo_timer: bool

    def __init__(self):
        self.details_to_stdout = False
        self.command_timeout = 0
        self.sudo_timer = False
