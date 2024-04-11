# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.helpers.ui
import pmb.config.pmaports


def is_systemd_selected(args):
    if "systemd" not in pmb.config.pmaports.read_config_repos(args):
        return False
    if pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd-never"):
        return False
    if args.systemd == "always":
        return True
    if args.systemd == "never":
        return False
    return pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd")


def systemd_selected_str(args):
    if "systemd" not in pmb.config.pmaports.read_config_repos(args):
        return "no", "not supported by pmaports branch"
    if pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd-never"):
        return "no", "not supported by selected UI"
    if args.systemd == "always":
        return "yes", "'always' selected in 'pmbootstrap init'"
    if args.systemd == "never":
        return "no", "'never' selected in 'pmbootstrap init'"
    if pmb.helpers.ui.check_option(args, args.ui, "pmb:systemd"):
        return "yes", "default for selected UI"
    return "no", "default for selected UI"
