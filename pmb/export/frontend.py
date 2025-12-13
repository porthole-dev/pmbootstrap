# Copyright 2017 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

import pmb.chroot.initfs
import pmb.export
import pmb.helpers.run
from pmb.core import Chroot, ChrootType
from pmb.core.context import get_context
from pmb.helpers import logging


def frontend(target: Path, autoinstall: bool, odin_flashable_tar: bool) -> None:
    config = get_context().config
    # Create the export folder
    if not os.path.exists(target):
        pmb.helpers.run.user(["mkdir", "-p", target])

    # Rootfs image note
    chroot = Chroot.native()
    rootfs_dir = chroot / "home/pmos/rootfs" / config.device
    if not rootfs_dir.glob("*.img"):
        logging.info(
            "NOTE: To export the rootfs image, run 'pmbootstrap"
            " install' first (without the 'disk' parameter)."
        )

    # Rebuild the initramfs, just to make sure (see #69)
    if autoinstall:
        pmb.chroot.initfs.build(Chroot(ChrootType.ROOTFS, config.device))

    # Do the export, print all files
    logging.info(f"Export symlinks to: {target}")
    if odin_flashable_tar:
        pmb.export.odin(config.device, target)
    pmb.export.symlinks(target)
