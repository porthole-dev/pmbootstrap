# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.helpers import logging
from pathlib import Path
import pmb.chroot.initfs_hooks
import pmb.chroot.other
import pmb.chroot.apk
import pmb.config.pmaports
from pmb.types import PmbArgs, RunOutputTypeDefault
import pmb.helpers.cli
from pmb.core import Chroot
from pmb.core.context import get_context


def build(chroot: Chroot) -> None:
    # Update mkinitfs and hooks
    pmb.chroot.apk.install(["postmarketos-mkinitfs"], chroot)
    pmb.chroot.initfs_hooks.update(chroot)

    # Call mkinitfs
    logging.info(f"({chroot}) mkinitfs")
    pmb.chroot.root(["mkinitfs"], chroot)


def extract(chroot: Chroot, extra: bool = False) -> Path:
    """
    Extract the initramfs to /tmp/initfs-extracted or the initramfs-extra to
    /tmp/initfs-extra-extracted and return the outside extraction path.
    """
    # Extraction folder
    inside = "/tmp/initfs-extracted"
    initfs_file = "/boot/initramfs"
    if extra:
        inside = "/tmp/initfs-extra-extracted"
        initfs_file += "-extra"

    outside = chroot / inside
    if outside.exists():
        if not pmb.helpers.cli.confirm(
            f"Extraction folder {outside} already exists. Do you want to overwrite it?"
        ):
            raise RuntimeError("Aborted!")
        pmb.chroot.root(["rm", "-r", inside], chroot)

    # Extraction script (because passing a file to stdin is not allowed
    # in pmbootstrap's chroot/shell functions for security reasons)
    with (chroot / "tmp/_extract.sh").open("w") as handle:
        handle.write(f"#!/bin/sh\ncd {inside} && cpio -i < _initfs\n")

    # Extract
    commands = [
        ["mkdir", "-p", inside],
        ["cp", initfs_file, f"{inside}/_initfs.gz"],
        ["gzip", "-d", f"{inside}/_initfs.gz"],
        ["cat", "/tmp/_extract.sh"],  # for the log
        ["sh", "/tmp/_extract.sh"],
        ["rm", "/tmp/_extract.sh", f"{inside}/_initfs"],
    ]
    for command in commands:
        pmb.chroot.root(command, chroot)

    # Return outside path for logging
    return outside


def ls(suffix: Chroot, extra: bool = False) -> None:
    tmp = "/tmp/initfs-extracted"
    if extra:
        tmp = "/tmp/initfs-extra-extracted"
    extract(suffix, extra)
    pmb.chroot.root(["ls", "-lahR", "."], suffix, Path(tmp), RunOutputTypeDefault.STDOUT)
    pmb.chroot.root(["rm", "-r", tmp], suffix)


def frontend(args: PmbArgs) -> None:
    context = get_context()
    chroot = Chroot.rootfs(context.config.device)
    deviceinfo = pmb.parse.deviceinfo()

    # Handle initfs actions
    action = args.action_initfs
    if action == "build":
        build(chroot)
    elif action == "extract":
        dir = extract(chroot)
        logging.info(f"Successfully extracted initramfs to: {dir}")
        if deviceinfo.create_initfs_extra:
            dir_extra = extract(chroot, True)
            logging.info(f"Successfully extracted initramfs-extra to: {dir_extra}")
    elif action == "ls":
        logging.info("*** initramfs ***")
        ls(chroot)
        if deviceinfo.create_initfs_extra:
            logging.info("*** initramfs-extra ***")
            ls(chroot, True)

    # Handle hook actions
    elif action == "hook_ls":
        pmb.chroot.initfs_hooks.ls(chroot)
    else:
        if action == "hook_add":
            pmb.chroot.initfs_hooks.add(args.hook, chroot)
        elif action == "hook_del":
            pmb.chroot.initfs_hooks.delete(args.hook, chroot)

        # Rebuild the initfs after adding/removing a hook
        build(chroot)

    if action in ["ls", "extract"]:
        link = "https://wiki.postmarketos.org/wiki/Initramfs_development"
        logging.info(f"See also: <{link}>")
