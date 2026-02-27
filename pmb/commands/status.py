# Copyright 2026 Hugo Posnic
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from typing import NoReturn

import pmb.helpers.status


def status() -> NoReturn:
    pmb.helpers.status.print_status()

    # Do not print the DONE! line
    sys.exit(0)
