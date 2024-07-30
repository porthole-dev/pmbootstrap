# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
import enum
from typing import Optional
from collections.abc import Generator
from pathlib import Path, PosixPath, PurePosixPath
from pmb.types import PmbArgs
from pmb.helpers import frontend

from .base import Command
from .log import Log
from .index import Index
from .repo_bootstrap import RepoBootstrap
from .shutdown import Shutdown
from .test import Test
from .pull import Pull
from .kconfig_check import KConfigCheck
from .kconfig_edit import KConfigEdit

"""New way to model pmbootstrap subcommands that can be invoked without PmbArgs."""

# Commands that are still invoked via pmb/helpers/frontend.py
unmigrated_commands = [
    "init",
    "work_migrate",
    "repo_missing",
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
]


def run_command(args: PmbArgs):
    # Handle deprecated command format
    if args.action in unmigrated_commands:
        getattr(frontend, args.action)(args)
        return

    command: Command
    # Would be nice to use match case but we support Python 3.8
    if args.action == "log":
        command = Log(args.clear_log, args.lines)
    elif args.action == "index":
        # FIXME: should index support --arch?
        command = Index()
    elif args.action == "repo_bootstrap":
        command = RepoBootstrap(args.arch, args.repository)
    elif args.action == "shutdown":
        command = Shutdown()
    elif args.action == "test":
        command = Test(args.action_test)
    elif args.action == "pull":
        command = Pull()
    elif args.action == "kconfig" and args.action_kconfig == "check":
        command = KConfigCheck(args.kconfig_check_details, args.file, args.package)
    elif args.action == "kconfig" and args.action_kconfig in ["edit", "migrate"]:
        command = KConfigEdit(args.package[0], args.action_kconfig == "migrate")
    else:
        raise NotImplementedError(f"Command '{args.action}' is not implemented.")

    command.run()
