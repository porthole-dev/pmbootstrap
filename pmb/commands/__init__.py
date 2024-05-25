# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
import enum
from typing import Generator, Optional
from pathlib import Path, PosixPath, PurePosixPath
import pmb.config
from pmb.types import PmbArgs
from pmb.helpers import frontend

from .base import Command
from .log import Log

"""New way to model pmbootstrap subcommands that can be invoked without PmbArgs."""

# Commands that are still invoked via pmb/helpers/frontend.py
unmigrated_commands = [
    "init",
    "shutdown",
    "index",
    "work_migrate",
    "repo_bootstrap",
    "repo_missing",
    "kconfig",
    "export",
    "sideload",
    "netboot",
    "flasher",
    "initfs",
    "qemu",
    "pkgrel_bump",
    "aportupgrade",
    "newapkbuild",
    "lint",
    "status",
    "ci",
    "zap",
    "stats",
    "update",
    "build_init",
    "chroot",
    "install",
    "checksum",
    "aportgen",
    "build",
    "deviceinfo_parse",
    "apkbuild_parse",
    "apkindex_parse",
    "config",
    "bootimg_analyze",
    "pull",
]

def run_command(args: PmbArgs):
    # Handle deprecated command format
    if args.action in unmigrated_commands:
        getattr(frontend, args.action)(args)
        return

    command: Command
    # FIXME: would be nice to use match case...
    if args.action == "log":
        command = Log(args.clear_log, int(args.lines))
    else:
        raise NotImplementedError(f"Command '{args.action}' is not implemented.")

    command.run()
