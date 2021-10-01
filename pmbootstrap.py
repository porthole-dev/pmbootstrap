#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
# PYTHON_ARGCOMPLETE_OK
import sys
version = sys.version_info
if version < (3, 6):
    print("You need at least Python 3.6 to run pmbootstrap")
    print("(You are running it with Python " + str(version.major) +
          "." + str(version.minor) + ")")
    sys.exit()
import pmb

if __name__ == "__main__":
    try:
        sys.exit(pmb.main())
    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt, exiting …")
        sys.exit(130)  # SIGINT(2) + 128
