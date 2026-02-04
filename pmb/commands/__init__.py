# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pmb.helpers import frontend
from pmb.types import PmbArgs

from .aportgen import Aportgen
from .base import Command
from .flasher import Flasher
from .index import Index
from .kconfig import KConfigCheck, KConfigEdit, KConfigGenerate, KConfigMigrate
from .log import Log
from .pkgrel_bump import PkgrelBump
from .pkgver_bump import PkgverBump
from .pull import Pull
from .shutdown import Shutdown
from .test import Test

"""New way to model pmbootstrap subcommands that can be invoked without PmbArgs."""

# Commands that are still invoked via pmb/helpers/frontend.py
unmigrated_commands = [
    "init",
    "work_migrate",
    "repo_missing",
    "export",
    "sideload",
    "netboot",
    "initfs",
    "qemu",
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
    "build",
    "apkbuild_parse",
    "apkindex_parse",
    "config",
    "bootimg_analyze",
]


def run_command(args: PmbArgs) -> None:
    # Handle deprecated command format
    if args.action in unmigrated_commands:
        getattr(frontend, args.action)(args)
        return

    command: Command
    match args.action:
        case "aportgen":
            command = Aportgen(args.packages, args.fork_alpine, args.fork_alpine_retain_branch)
        case "flasher":
            command = Flasher(
                args.action_flasher,
                # FIXME: defaults copied from pmb/helpers/arguments.py
                # we should have these defaults defined in one place!
                getattr(args, "autoinstall", True),
                getattr(args, "cmdline", None),
                args.flash_method,
                getattr(args, "no_reboot", None),
                getattr(args, "partition", None),
                getattr(args, "resume", None),
            )
        case "log":
            command = Log(args.clear_log, args.lines)
        case "index":
            # FIXME: should index support --arch?
            command = Index()
        case "shutdown":
            command = Shutdown()
        case "test":
            command = Test(args.action_test)
        case "pkgrel_bump":
            command = PkgrelBump(args.packages, args.dry, args.auto)
        case "pkgver_bump":
            command = PkgverBump(args.packages)
        case "pull":
            command = Pull()
        case "kconfig":
            match args.action_kconfig:
                case "check":
                    categories = args.categories.split(",") if args.categories else []
                    command = KConfigCheck(
                        args.kconfig_check_details,
                        args.file,
                        args.package,
                        args.keep_going,
                        categories,
                    )
                case "edit":
                    command = KConfigEdit(
                        args.package[0], args.arch, args.xconfig, args.nconfig, args.fragment
                    )
                case "migrate":
                    command = KConfigMigrate(args.package, args.arch)
                case "generate":
                    command = KConfigGenerate(args.package, args.arch)

        case _:
            raise NotImplementedError(f"Command '{args.action}' is not implemented.")

    command.run()
