# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.helpers import logging
from pathlib import Path
from typing import List

import pmb.build
import pmb.chroot.apk
import pmb.config
import pmb.config.pmaports
from pmb.types import PmbArgs
import pmb.flasher
import pmb.helpers.file
from pmb.core import Chroot, ChrootType


def symlinks(args: PmbArgs, flavor, folder: Path):
    """
    Create convenience symlinks to the rootfs and boot files.
    """

    # Backwards compatibility with old mkinitfs (pma#660)
    suffix = f"-{flavor}"
    pmaports_cfg = pmb.config.pmaports.read_config()
    if pmaports_cfg.get("supported_mkinitfs_without_flavors", False):
        suffix = ""

    # File descriptions
    info = {
        f"boot.img{suffix}": ("Fastboot compatible boot.img file,"
                              " contains initramfs and kernel"),
        "dtbo.img": "Fastboot compatible dtbo image",
        f"initramfs{suffix}": "Initramfs",
        f"initramfs{suffix}-extra": "Extra initramfs files in /boot",
        f"uInitrd{suffix}": "Initramfs, legacy u-boot image format",
        f"uImage{suffix}": "Kernel, legacy u-boot image format",
        f"vmlinuz{suffix}": "Linux kernel",
        f"{args.device}.img": "Rootfs with partitions for /boot and /",
        f"{args.device}-boot.img": "Boot partition image",
        f"{args.device}-root.img": "Root partition image",
        f"pmos-{args.device}.zip": "Android recovery flashable zip",
        "lk2nd.img": "Secondary Android bootloader",
    }

    # Generate a list of patterns
    chroot_native = Chroot.native()
    path_boot = Chroot(ChrootType.ROOTFS, args.device) / "boot"
    chroot_buildroot = Chroot.buildroot(args.deviceinfo['arch'])
    files: List[Path] = [
        path_boot / f"boot.img{suffix}",
        path_boot / f"uInitrd{suffix}",
        path_boot / f"uImage{suffix}",
        path_boot / f"vmlinuz{suffix}",
        path_boot /  "dtbo.img",
        chroot_native / "home/pmos/rootfs" / f"{args.device}.img",
        chroot_native / "home/pmos/rootfs" / f"{args.device}-boot.img",
        chroot_native / "home/pmos/rootfs" / f"{args.device}-root.img",
        chroot_buildroot / "var/libpostmarketos-android-recovery-installer" /
            f"pmos-{args.device}.zip",
        path_boot / "lk2nd.img"
    ]

    files += list(path_boot.glob(f"initramfs{suffix}*"))

    # Iterate through all files
    for file in files:
        basename = file.name
        link = folder / basename

        # Display a readable message
        msg = " * " + basename
        if basename in info:
            msg += " (" + info[basename] + ")"
        logging.info(msg)

        pmb.helpers.file.symlink(args, file, link)
