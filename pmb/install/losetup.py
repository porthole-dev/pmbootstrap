# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import glob
import json
from pathlib import Path
from typing import List, Optional
from pmb.helpers import logging
import os
import time

from pmb.types import PathString, PmbArgs
import pmb.helpers.mount
import pmb.helpers.run
import pmb.chroot
from pmb.core import Chroot


def init(args: PmbArgs):
    if not Path("/sys/module/loop").is_dir():
        pmb.helpers.run.root(["modprobe", "loop"])
    for loopdevice in Path("/dev/").glob("loop*"):
        if loopdevice.is_dir():
            continue
        pmb.helpers.mount.bind_file(loopdevice, Chroot.native() / loopdevice)


def mount(args: PmbArgs, img_path: Path):
    """
    :param img_path: Path to the img file inside native chroot.
    """
    logging.debug(f"(native) mount {img_path} (loop)")

    # Try to mount multiple times (let the kernel module initialize #1594)
    for i in range(0, 5):
        # Retry
        if i > 0:
            logging.debug("loop module might not be initialized yet, retry in"
                          " one second...")
            time.sleep(1)

        # Mount and return on success
        init(args)

        losetup_cmd: List[PathString] = ["losetup", "-f", img_path]
        sector_size = args.deviceinfo["rootfs_image_sector_size"]
        if sector_size:
            losetup_cmd += ["-b", str(int(sector_size))]

        pmb.chroot.root(losetup_cmd, check=False)
        try:
            device_by_back_file(args, img_path)
            return
        except RuntimeError:
            pass

    # Failure: raise exception
    raise RuntimeError(f"Failed to mount loop device: {img_path}")


def device_by_back_file(back_file: Path) -> Path:
    """
    Get the /dev/loopX device that points to a specific image file.
    """

    # Get list from losetup
    losetup_output = pmb.chroot.root(["losetup", "--json", "--list"],
                                     output_return=True)
    if not losetup_output:
        raise RuntimeError("losetup failed")

    # Find the back_file
    losetup = json.loads(losetup_output)
    for loopdevice in losetup["loopdevices"]:
        if Path(loopdevice["back-file"]) == back_file:
            return Path(loopdevice["name"])
    raise RuntimeError(f"Failed to find loop device for {back_file}")


def umount(img_path: Path):
    """
    :param img_path: Path to the img file inside native chroot.
    """
    device: Path
    try:
        device = device_by_back_file(img_path)
    except RuntimeError:
        return
    logging.debug(f"(native) umount {device}")
    pmb.chroot.root(["losetup", "-d", device])
