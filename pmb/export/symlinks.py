# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.core.context import get_context
from pmb.helpers import logging
from pathlib import Path

import pmb.build
import pmb.chroot.apk
import pmb.flasher
import pmb.helpers.file
from pmb.core import Chroot, ChrootType


def symlinks(folder: Path) -> None:
    """
    Create convenience symlinks to the rootfs and boot files.
    """

    device = get_context().config.device
    arch = pmb.parse.deviceinfo(device).arch

    # File descriptions
    info = {
        "boot.img": (
            "Fastboot compatible boot.img file, contains initramfs with bootimg header <=2 and kernel"
        ),
        "vendor_boot.img": (
            "Fastboot compatible vendor_boot.img file, contains cmdline, initramfs and dtb. Only with bootimg header >= v3"
        ),
        "dtbo.img": "Fastboot compatible dtbo image",
        "initramfs": "Initramfs",
        "initramfs-extra": "Extra initramfs files in /boot",
        "uInitrd": "Initramfs, legacy u-boot image format",
        "uImage": "Kernel, legacy u-boot image format",
        "vmlinuz": "Linux kernel",
        f"{device}.img": "Rootfs with partitions for /boot and /",
        f"{device}-boot.img": "Boot partition image",
        f"{device}-root.img": "Root partition image",
        f"pmos-{device}.zip": "Android recovery flashable zip",
        "lk2nd.img": "Secondary Android bootloader",
    }

    # Generate a list of patterns
    chroot_native = Chroot.native()
    path_boot = Chroot(ChrootType.ROOTFS, device) / "boot"
    chroot_buildroot = Chroot.buildroot(arch)
    files: list[Path] = [
        path_boot / "boot.img",
        path_boot / "vendor_boot.img",
        path_boot / "uInitrd",
        path_boot / "uImage",
        path_boot / "dtbo.img",
        chroot_native / "home/pmos/rootfs" / f"{device}.img",
        chroot_native / "home/pmos/rootfs" / f"{device}-boot.img",
        chroot_native / "home/pmos/rootfs" / f"{device}-root.img",
        chroot_buildroot / "var/lib/postmarketos-android-recovery-installer" / f"pmos-{device}.zip",
        path_boot / "lk2nd.img",
    ]

    files += list(path_boot.glob("initramfs*"))
    files += list(path_boot.glob("vmlinuz*"))

    # Iterate through all files
    for file in files:
        basename = file.name
        link = folder / basename

        # Display a readable message
        msg = " * " + basename
        if basename in info:
            msg += " (" + info[basename] + ")"
        logging.info(msg)

        pmb.helpers.file.symlink(file, link)
