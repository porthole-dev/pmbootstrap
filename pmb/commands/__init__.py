# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pmb.core.context import get_context
from pmb.helpers import frontend
from pmb.types import PmbArgs

from .aportgen import aportgen
from .build import build
from .checksum import checksum
from .ci import ci
from .config import config
from .export import export
from .flasher import flasher
from .index import index
from .kconfig import KConfigCheck, KConfigEdit, KConfigGenerate, KConfigMigrate
from .log import log
from .netboot import netboot
from .pkgrel_bump import pkgrel_bump
from .pkgver_bump import pkgver_bump
from .pull import pull
from .shutdown import shutdown
from .sideload import sideload
from .status import status
from .test import test
from .zap import zap

"""New way to model pmbootstrap subcommands that can be invoked without PmbArgs."""

# Commands that are still invoked via pmb/helpers/frontend.py
unmigrated_commands = [
    "init",
    "work_migrate",
    "repo_missing",
    "initfs",
    "qemu",
    "newapkbuild",
    "stats",
    "update",
    "build_init",
    "chroot",
    "install",
    "apkbuild_parse",
    "apkindex_parse",
    "bootimg_analyze",
]


def run_command(args: PmbArgs) -> None:
    # Handle deprecated command format
    if args.action in unmigrated_commands:
        getattr(frontend, args.action)(args)
        return

    match args.action:
        case "aportgen":
            aportgen(args.packages, args.fork_alpine, args.fork_alpine_retain_branch)
        case "build":
            build(args.packages, args.arch, args.src, args.envkernel, args.strict)
        case "checksum":
            checksum(args.packages, args.changed, args.verify)
        case "ci":
            ci(args.scripts, args.all, args.fast)
        case "config":
            config(args.name, args.value, args.reset, args.config)
        case "export":
            export(args.export_folder, args.autoinstall, args.odin_flashable_tar)
        case "flasher":
            flasher(
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
            log(args.clear_log, args.lines)
        case "index":
            # FIXME: should index support --arch?
            index()
        case "shutdown":
            shutdown()
        case "sideload":
            sideload(
                args.user or get_context().config.user,
                args.host,
                str(args.port),
                args.arch,
                args.install_key,
                args.packages,
            )
        case "test":
            test(args.action_test)
        case "netboot":
            netboot(args.action_netboot, args.replace)
        case "pkgrel_bump":
            pkgrel_bump(args.packages, args.dry, args.auto)
        case "pkgver_bump":
            pkgver_bump(args.packages)
        case "pull":
            pull()
        case "kconfig":
            match args.action_kconfig:
                case "check":
                    categories = args.categories.split(",") if args.categories else []
                    KConfigCheck(
                        args.kconfig_check_details,
                        args.file,
                        args.package,
                        args.keep_going,
                        categories,
                    ).run()
                case "edit":
                    KConfigEdit(
                        args.package[0], args.arch, args.xconfig, args.nconfig, args.fragment
                    ).run()
                case "migrate":
                    KConfigMigrate(args.package, args.arch).run()
                case "generate":
                    KConfigGenerate(args.package, args.arch).run()
        case "status":
            status()
        case "zap":
            zap(
                args.dry,
                args.http,
                args.distfiles,
                args.pkgs_local,
                args.pkgs_local_mismatch,
                args.pkgs_online_mismatch,
                args.rust,
                args.netboot,
            )
        case _:
            raise NotImplementedError(f"Command '{args.action}' is not implemented.")
