# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.config.pmaports
import pmb.helpers.ui
from pmb.core import Config
from pmb.core.config import SystemdConfig
from pmb.meta import Cache


@Cache()
def is_systemd_selected(config: Config) -> bool:
    if "systemd" not in pmb.config.pmaports.read_config_repos():
        return False
    if pmb.helpers.ui.check_option(
        config.ui, "pmb:systemd-never", with_extra_repos="disabled", must_exist=False
    ):
        return False
    if config.systemd == SystemdConfig.ALWAYS:
        return True
    if config.systemd == SystemdConfig.NEVER:
        return False
    current_ui_needs_systemd = pmb.helpers.ui.check_option(
        config.ui, "pmb:systemd", with_extra_repos="disabled", must_exist=False
    )

    return current_ui_needs_systemd if current_ui_needs_systemd is not None else False


def systemd_selected_str(config: Config) -> tuple[str, str]:
    if "systemd" not in pmb.config.pmaports.read_config_repos():
        return "no", "not supported by pmaports branch"
    if pmb.helpers.ui.check_option(config.ui, "pmb:systemd-never", must_exist=False):
        return "no", "not supported by selected UI"
    if config.systemd == SystemdConfig.ALWAYS:
        return "yes", "'always' selected in 'pmbootstrap init'"
    if config.systemd == SystemdConfig.NEVER:
        return "no", "'never' selected in 'pmbootstrap init'"
    if pmb.helpers.ui.check_option(config.ui, "pmb:systemd", must_exist=False):
        return "yes", "default for selected UI"
    return "no", "default for selected UI"
