# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import glob

import pmb.build
import pmb.chroot.apk
import pmb.config
import pmb.flasher
import pmb.helpers.file


def symlinks(args, flavor, folder):
    """
    Create convenience symlinks to the rootfs and boot files.
    """

    # File descriptions
    info = {
        "boot.img-" + flavor: "Fastboot compatible boot.img file,"
        " contains initramfs and kernel",
        "initramfs-" + flavor: "Initramfs",
        "initramfs-" + flavor + "-extra": "Extra initramfs files in /boot",
        "uInitrd-" + flavor: "Initramfs, legacy u-boot image format",
        "uImage-" + flavor: "Kernel, legacy u-boot image format",
        "vmlinuz-" + flavor: "Linux kernel",
        args.device + ".img": "Rootfs with partitions for /boot and /",
        args.device + "-boot.img": "Boot partition image",
        args.device + "-root.img": "Root partition image",
        "pmos-" + args.device + ".zip": "Android recovery flashable zip",
    }

    # Generate a list of patterns
    path_native = args.work + "/chroot_native"
    path_boot = args.work + "/chroot_rootfs_" + args.device + "/boot"
    path_buildroot = args.work + "/chroot_buildroot_" + args.deviceinfo["arch"]
    patterns = [path_boot + "/*-" + flavor,
                path_boot + "/*-" + flavor + "-extra",
                path_native + "/home/pmos/rootfs/" + args.device + ".img",
                path_native + "/home/pmos/rootfs/" + args.device + "-boot.img",
                path_native + "/home/pmos/rootfs/" + args.device + "-root.img",
                path_buildroot +
                "/var/lib/postmarketos-android-recovery-installer/pmos-" +
                args.device + ".zip"]

    # Generate a list of files from the patterns
    files = []
    for pattern in patterns:
        files += glob.glob(pattern)

    # Iterate through all files
    for file in files:
        basename = os.path.basename(file)
        link = folder + "/" + basename

        # Display a readable message
        msg = " * " + basename
        if basename in info:
            msg += " (" + info[basename] + ")"
        logging.info(msg)

        pmb.helpers.file.symlink(args, file, link)
