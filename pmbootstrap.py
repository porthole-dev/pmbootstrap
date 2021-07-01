#!/usr/bin/env python3
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
# PYTHON_ARGCOMPLETE_OK
import sys
import pmb

if __name__ == "__main__":
    try:
        sys.exit(pmb.main())
    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt, exiting …")
        sys.exit(130)  # SIGINT(2) + 128
