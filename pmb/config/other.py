# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.types import Config
import pmb.helpers.ui
import pmb.config.pmaports


def is_systemd_selected(config: Config):
    if "systemd" not in pmb.config.pmaports.read_config_repos():
        return False
    if pmb.helpers.ui.check_option(config.ui, "pmb:systemd-never"):
        return False
    if config.systemd == "always":
        return True
    if config.systemd == "never":
        return False
    return pmb.helpers.ui.check_option(config.ui, "pmb:systemd")


def systemd_selected_str(config: Config):
    if "systemd" not in pmb.config.pmaports.read_config_repos():
        return "no", "not supported by pmaports branch"
    if pmb.helpers.ui.check_option(config.ui, "pmb:systemd-never"):
        return "no", "not supported by selected UI"
    if config.systemd == "always":
        return "yes", "'always' selected in 'pmbootstrap init'"
    if config.systemd == "never":
        return "no", "'never' selected in 'pmbootstrap init'"
    if pmb.helpers.ui.check_option(config.ui, "pmb:systemd"):
        return "yes", "default for selected UI"
    return "no", "default for selected UI"
