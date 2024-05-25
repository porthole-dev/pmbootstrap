# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.config
import pmb.config.workdir
import pmb.helpers.git
from pmb.types import Config, PmbArgs
from pmb.core import get_context
from typing import List, Tuple


def print_status_line(key: str, value: str):
    styles = pmb.config.styles
    key = f"{styles['GREEN']}{key}{styles['END']}:"
    padding = 17

    print(f"{key.ljust(padding)} {value}")


def print_channel(config: Config) -> None:
    pmaports_cfg = pmb.config.pmaports.read_config()
    channel = pmaports_cfg["channel"]

    # Get branch name (if on branch) or current commit
    path = pmb.helpers.git.get_path("pmaports")
    ref = pmb.helpers.git.rev_parse(path, extra_args=["--abbrev-ref"])
    if ref == "HEAD":
        ref = pmb.helpers.git.rev_parse(path)[0:8]

    if not pmb.helpers.git.clean_worktree(path):
        ref += ", dirty"

    value = f"{channel} (pmaports: {ref})"
    print_status_line("Channel", value)


def print_device(args: PmbArgs, config: Config) -> None:
    kernel = ""
    if pmb.parse._apkbuild.kernels(config.device):
        kernel = f", kernel: {config.kernel}"

    value = f"{config.device} ({args.deviceinfo['arch']}{kernel})"
    print_status_line("Device", value)


def print_ui(config: Config) -> None:
    print_status_line("UI", config.ui)


def print_systemd(config: Config) -> None:
    yesno, reason = pmb.config.other.systemd_selected_str(config)
    print_status_line("systemd", f"{yesno} ({reason})")


def print_status(args: PmbArgs) -> None:
    """ :param details: if True, print each passing check instead of a summary
        :returns: True if all checks passed, False otherwise """
    config = get_context().config
    print_channel(config)
    print_device(args, config)
    print_ui(config)
    print_systemd(config)
