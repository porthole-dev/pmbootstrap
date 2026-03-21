# Copyright 2026 Oliver Smith, Paul Adam
# SPDX-License-Identifier: GPL-3.0-or-later
from getpass import getpass

import pmb.config
import pmb.install
import pmb.parse
from pmb.core.context import get_context
from pmb.helpers import logging
from pmb.helpers.exceptions import NonBugError
from pmb.types import PmbArgs


def install(args: PmbArgs) -> None:
    config = get_context().config
    device = config.device
    deviceinfo = pmb.parse.deviceinfo(device)
    is_split = args.split if args.split is not None else False
    if args.no_fde:
        logging.warning("WARNING: --no-fde is deprecated, as it is now the default.")
    if args.rsync and args.full_disk_encryption:
        raise ValueError("Installation using rsync is not compatible with full disk encryption.")
    if args.rsync and not args.disk:
        raise ValueError("Installation using rsync only works with --disk.")

    if args.rsync and args.filesystem == "btrfs":
        raise ValueError("Installation using rsync is not currently supported on btrfs filesystem.")

    if not args.disk and args.split is None:
        # Default to split if the flash method requires it
        flasher = pmb.config.flashers.get(deviceinfo.flash_method, {})
        if flasher.get("split", False):
            is_split = True

    # Android recovery zip related
    if args.android_recovery_zip and args.filesystem:
        raise ValueError(
            "--android-recovery-zip cannot be combined with --filesystem (patches welcome)"
        )
    if args.android_recovery_zip and args.full_disk_encryption:
        logging.info(
            "WARNING: --fde is rarely used in combination with"
            " --android-recovery-zip. If this does not work, consider"
            " using another method (e.g. installing via netcat)"
        )
        logging.info(
            "WARNING: the kernel of the recovery system (e.g. TWRP)"
            f" must support the cryptsetup cipher '{args.cipher}'."
        )
        logging.info(
            "If you know what you are doing, consider setting a"
            " different cipher with 'pmbootstrap install --cipher=..."
            " --fde --android-recovery-zip'."
        )

    # Don't install locally compiled packages and package signing keys
    if not args.install_local_pkgs:
        # Implies that we don't build outdated packages (overriding the answer
        # in 'pmbootstrap init')
        config.build_pkgs_on_install = False

        # Safest way to avoid installing local packages is having none
        if list((config.work / "packages").glob("*")):
            raise ValueError(
                "--no-local-pkgs specified, but locally built"
                " packages found. Consider 'pmbootstrap zap -p'"
                " to delete them."
            )

    if not args.password:
        args.password = getpass(f"Choose a password for the user '{config.user}': ")
        if getpass(f"Confirm password for '{config.user}': ") != args.password:
            raise NonBugError("Passwords did not match!")

    # Verify that the root filesystem is supported by current pmaports branch
    pmb.install.get_root_filesystem(args.filesystem)

    pmb.install.install(
        args.add,
        args.android_recovery_zip,
        args.cipher,
        getattr(args, "cmdline", None),
        args.filesystem,
        args.full_disk_encryption,
        args.disk,
        args.install_base,
        args.install_cgpt,
        args.install_local_pkgs,
        args.install_recommends,
        args.iter_time,
        args.no_firewall,
        args.no_image,
        getattr(args, "no_reboot", None),
        args.no_sshd,
        getattr(args, "partition", None),
        args.password,
        args.recovery_flash_kernel,
        args.recovery_install_partition,
        getattr(args, "resume", None),
        args.rsync,
        args.sector_size,
        args.single_partition,
        args.sparse,
        args.verbose,
        args.zap,
        is_split,
    )
