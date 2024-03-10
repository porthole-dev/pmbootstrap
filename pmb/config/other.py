# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.helpers.ui


def is_systemd_selected(args):
    if pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd-never"):
        return False
    if args.systemd == "always":
        return True
    if args.systemd == "never":
        return False
    return pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd")
