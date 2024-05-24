# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.config
import pmb.config.workdir
import pmb.helpers.git
from pmb.core.types import PmbArgs
from typing import List, Tuple


def print_status_line(key: str, value: str):
    styles = pmb.config.styles
    key = f"{styles['GREEN']}{key}{styles['END']}:"
    padding = 17

    print(f"{key.ljust(padding)} {value}")


def print_channel(args: PmbArgs) -> None:
    pmaports_cfg = pmb.config.pmaports.read_config(args)
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


def print_device(args: PmbArgs) -> None:
    kernel = ""
    if pmb.parse._apkbuild.kernels(args, args.device):
        kernel = f", kernel: {args.kernel}"

    value = f"{args.device} ({args.deviceinfo['arch']}{kernel})"
    print_status_line("Device", value)


def print_ui(args: PmbArgs) -> None:
    print_status_line("UI", args.ui)


def print_systemd(args: PmbArgs) -> None:
    yesno, reason = pmb.config.other.systemd_selected_str(args)
    print_status_line("systemd", f"{yesno} ({reason})")


def print_status(args: PmbArgs) -> None:
    """ :param details: if True, print each passing check instead of a summary
        :returns: True if all checks passed, False otherwise """
    print_channel(args)
    print_device(args)
    print_ui(args)
    print_systemd(args)
