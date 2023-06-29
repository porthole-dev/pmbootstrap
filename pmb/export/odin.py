# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from pathlib import Path

import pmb.build
import pmb.chroot.apk
import pmb.config
from pmb.core.types import PmbArgs
import pmb.flasher
import pmb.helpers.file
from pmb.core import Chroot, ChrootType


def odin(args: PmbArgs, flavor, folder: Path):
    """
    Create Odin flashable tar file with kernel and initramfs
    for devices configured with the flasher method 'heimdall-isorec'
    and with boot.img for devices with 'heimdall-bootimg'
    """
    pmb.flasher.init(args)
    suffix = Chroot(ChrootType.ROOTFS, args.device)

    # Backwards compatibility with old mkinitfs (pma#660)
    suffix_flavor = f"-{flavor}"
    pmaports_cfg = pmb.config.pmaports.read_config(args)
    if pmaports_cfg.get("supported_mkinitfs_without_flavors", False):
        suffix_flavor = ""

    # Validate method
    method = args.deviceinfo["flash_method"]
    if not method.startswith("heimdall-"):
        raise RuntimeError("An odin flashable tar is not supported"
                           f" for the flash method '{method}' specified"
                           " in the current configuration."
                           " Only 'heimdall' methods are supported.")

    # Partitions
    partition_kernel = \
        args.deviceinfo["flash_heimdall_partition_kernel"] or "KERNEL"
    partition_initfs = \
        args.deviceinfo["flash_heimdall_partition_initfs"] or "RECOVERY"

    # Temporary folder
    temp_folder = "/tmp/odin-flashable-tar"
    if (Chroot.native() / temp_folder).exists():
        pmb.chroot.root(args, ["rm", "-rf", temp_folder])

    # Odin flashable tar generation script
    # (because redirecting stdin/stdout is not allowed
    # in pmbootstrap's chroot/shell functions for security reasons)
    odin_script = Chroot(ChrootType.ROOTFS, args.device) / "tmp/_odin.sh"
    with odin_script.open("w") as handle:
        odin_kernel_md5 = f"{partition_kernel}.bin.md5"
        odin_initfs_md5 = f"{partition_initfs}.bin.md5"
        odin_device_tar = f"{args.device}.tar"
        odin_device_tar_md5 = f"{args.device}.tar.md5"

        handle.write(
            "#!/bin/sh\n"
            f"cd {temp_folder}\n")
        if method == "heimdall-isorec":
            handle.write(
                # Kernel: copy and append md5
                f"cp /boot/vmlinuz{suffix_flavor} {odin_kernel_md5}\n"
                f"md5sum -t {odin_kernel_md5} >> {odin_kernel_md5}\n"
                # Initramfs: recompress with lzop, append md5
                f"gunzip -c /boot/initramfs{suffix_flavor}"
                f" | lzop > {odin_initfs_md5}\n"
                f"md5sum -t {odin_initfs_md5} >> {odin_initfs_md5}\n")
        elif method == "heimdall-bootimg":
            handle.write(
                # boot.img: copy and append md5
                f"cp /boot/boot.img{suffix_flavor} {odin_kernel_md5}\n"
                f"md5sum -t {odin_kernel_md5} >> {odin_kernel_md5}\n")
        handle.write(
            # Create tar, remove included files and append md5
            f"tar -c -f {odin_device_tar} *.bin.md5\n"
            "rm *.bin.md5\n"
            f"md5sum -t {odin_device_tar} >> {odin_device_tar}\n"
            f"mv {odin_device_tar} {odin_device_tar_md5}\n")

    commands = [["mkdir", "-p", temp_folder],
                ["cat", "/tmp/_odin.sh"],  # for the log
                ["sh", "/tmp/_odin.sh"],
                ["rm", "/tmp/_odin.sh"]
                ]
    for command in commands:
        pmb.chroot.root(args, command, suffix)

    # Move Odin flashable tar to native chroot and cleanup temp folder
    pmb.chroot.user(args, ["mkdir", "-p", "/home/pmos/rootfs"])
    pmb.chroot.root(args, ["mv", f"/mnt/rootfs_{args.device}{temp_folder}"
                           f"/{odin_device_tar_md5}", "/home/pmos/rootfs/"]),
    pmb.chroot.root(args, ["chown", "pmos:pmos",
                           f"/home/pmos/rootfs/{odin_device_tar_md5}"])
    pmb.chroot.root(args, ["rmdir", temp_folder], suffix)

    # Create the symlink
    file = Chroot.native() / "home/pmos/rootfs" / odin_device_tar_md5
    link = folder / odin_device_tar_md5
    pmb.helpers.file.symlink(args, file, link)

    # Display a readable message
    msg = f" * {odin_device_tar_md5}"
    if method == "heimdall-isorec":
        msg += " (Odin flashable file, contains initramfs and kernel)"
    elif method == "heimdall-bootimg":
        msg += " (Odin flashable file, contains boot.img)"
    logging.info(msg)
