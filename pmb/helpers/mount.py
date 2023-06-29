# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path, PurePath
from typing import List
from pmb.core.types import PmbArgs
import pmb.helpers
from pmb.core import Chroot
import pmb.helpers.run


def ismount(folder: Path):
    """Ismount() implementation that works for mount --bind.

    Workaround for: https://bugs.python.org/issue29707
    """
    folder = folder.resolve()
    with open("/proc/mounts", "r") as handle:
        for line in handle:
            words = line.split()
            if len(words) >= 2 and Path(words[1]) == folder:
                return True
            if words[0] == folder:
                return True
    return False


def bind(args: PmbArgs, source: Path, destination: Path, create_folders=True, umount=False):
    """Mount --bind a folder and create necessary directory structure.

    :param umount: when destination is already a mount point, umount it first.
    """
    # Check/umount destination
    if ismount(destination):
        if umount:
            umount_all(args, destination)
        else:
            return

    # Check/create folders
    for path in [source, destination]:
        if os.path.exists(path):
            continue
        if create_folders:
            pmb.helpers.run.root(args, ["mkdir", "-p", path])
        else:
            raise RuntimeError("Mount failed, folder does not exist: " +
                               path)

    # Actually mount the folder
    pmb.helpers.run.root(args, ["mount", "--bind", source, destination])

    # Verify that it has worked
    if not ismount(destination):
        raise RuntimeError(f"Mount failed: {source} -> {destination}")


def bind_file(args: PmbArgs, source: Path, destination: Path, create_folders=False):
    """Mount a file with the --bind option, and create the destination file, if necessary."""
    # Skip existing mountpoint
    if ismount(destination):
        return

    # Create empty file
    if not destination.exists():
        if create_folders:
            dest_dir: Path = destination.parent
            if not dest_dir.is_dir():
                pmb.helpers.run.root(args, ["mkdir", "-p", dest_dir])

        pmb.helpers.run.root(args, ["touch", destination])

    # Mount
    pmb.helpers.run.root(args, ["mount", "--bind", source,
                                destination])


def umount_all_list(prefix: Path, source: Path=Path("/proc/mounts")) -> List[Path]:
    """Parse `/proc/mounts` for all folders beginning with a prefix.

    :source: can be changed for testcases

    :returns: a list of folders that need to be umounted

    """
    ret = []
    prefix = prefix.resolve()
    with source.open() as handle:
        for line in handle:
            words = line.split()
            if len(words) < 2:
                raise RuntimeError("Failed to parse line in " + source + ": " +
                                   line)
            mountpoint = Path(words[1].replace(r"\040(deleted)", ""))
            if mountpoint.is_relative_to(prefix): # is subpath
                ret.append(mountpoint)
    ret.sort(reverse=True)
    return ret


def umount_all(args: PmbArgs, folder: Path):
    """Umount all folders that are mounted inside a given folder."""
    for mountpoint in umount_all_list(folder):
        pmb.helpers.run.root(args, ["umount", mountpoint])
        if ismount(mountpoint):
            raise RuntimeError("Failed to umount: " + mountpoint)


def mount_device_rootfs(args: PmbArgs, chroot_rootfs: Chroot) -> PurePath:
    """
    Mount the device rootfs.
    :param chroot_rootfs: the chroot where the rootfs that will be
                          installed on the device has been created (e.g.
                          "rootfs_qemu-amd64")
    :returns: the mountpoint (relative to the native chroot)
    """
    mountpoint = PurePath("/mnt", chroot_rootfs.dirname())
    pmb.helpers.mount.bind(args, chroot_rootfs.path,
                           Chroot.native() / mountpoint)
    return mountpoint
