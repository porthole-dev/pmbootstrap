# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.helpers import logging
import os
from pathlib import Path
from typing import Dict
import pmb.config
from pmb.core.types import PmbArgs
import pmb.parse
import pmb.helpers.mount
from pmb.core import Chroot


def create_device_nodes(args: PmbArgs, chroot: Chroot):
    """
    Create device nodes for null, zero, full, random, urandom in the chroot.
    """
    try:
        # Create all device nodes as specified in the config
        for dev in pmb.config.chroot_device_nodes:
            path = chroot / "dev" / str(dev[4])
            if not path.exists():
                pmb.helpers.run.root(args, ["mknod",
                                            "-m", str(dev[0]),  # permissions
                                            path,  # name
                                            str(dev[1]),  # type
                                            str(dev[2]),  # major
                                            str(dev[3]),  # minor
                                            ])

        # Verify major and minor numbers of created nodes
        for dev in pmb.config.chroot_device_nodes:
            path = chroot / "dev" / str(dev[4])
            stat_result = path.stat()
            rdev = stat_result.st_rdev
            assert os.major(rdev) == dev[2], f"Wrong major in {path}"
            assert os.minor(rdev) == dev[3], f"Wrong minor in {path}"

        # Verify /dev/zero reading and writing
        path = chroot / "dev/zero"
        with open(path, "r+b", 0) as handle:
            assert handle.write(bytes([0xff])), f"Write failed for {path}"
            assert handle.read(1) == bytes([0x00]), f"Read failed for {path}"

    # On failure: Show filesystem-related error
    except Exception as e:
        logging.info(str(e) + "!")
        raise RuntimeError(f"Failed to create device nodes in the '{chroot}' chroot.")


def mount_dev_tmpfs(args: PmbArgs, chroot: Chroot=Chroot.native()):
    """
    Mount tmpfs inside the chroot's dev folder to make sure we can create
    device nodes, even if the filesystem of the work folder does not support
    it.
    """
    # Do nothing when it is already mounted
    dev = chroot / "dev"
    if pmb.helpers.mount.ismount(dev):
        return

    # Create the $chroot/dev folder and mount tmpfs there
    pmb.helpers.run.root(args, ["mkdir", "-p", dev])
    pmb.helpers.run.root(args, ["mount", "-t", "tmpfs",
                                "-o", "size=1M,noexec,dev",
                                "tmpfs", dev])

    # Create pts, shm folders and device nodes
    pmb.helpers.run.root(args, ["mkdir", "-p", dev / "pts", dev / "shm"])
    pmb.helpers.run.root(args, ["mount", "-t", "tmpfs",
                                "-o", "nodev,nosuid,noexec",
                                "tmpfs", dev / "shm"])
    create_device_nodes(args, chroot)

    # Setup /dev/fd as a symlink
    pmb.helpers.run.root(args, ["ln", "-sf", "/proc/self/fd", f"{dev}/"])


def mount(args: PmbArgs, chroot: Chroot=Chroot.native()):
    # Mount tmpfs as the chroot's /dev
    mount_dev_tmpfs(args, chroot)

    # Get all mountpoints
    arch = pmb.parse.arch.from_chroot_suffix(args, chroot)
    channel = pmb.config.pmaports.read_config(args)["channel"]
    mountpoints: Dict[Path, Path] = {}
    for src_template, target_template in pmb.config.chroot_mount_bind.items():
        src_template = src_template.replace("$WORK", os.fspath(pmb.config.work))
        src_template = src_template.replace("$ARCH", arch)
        src_template = src_template.replace("$CHANNEL", channel)
        mountpoints[Path(src_template)] = Path(target_template)

    # Mount if necessary
    for source, target in mountpoints.items():
        target_outer = chroot / target
        #raise RuntimeError("test")
        pmb.helpers.mount.bind(args, source, target_outer)


def mount_native_into_foreign(args: PmbArgs, chroot: Chroot):
    source = Chroot.native().path
    target = chroot / "native"
    pmb.helpers.mount.bind(args, source, target)

    musl = next(source.glob("lib/ld-musl-*.so.1")).name
    musl_link = (chroot / "lib" / musl)
    if not musl_link.is_symlink():
        pmb.helpers.run.root(args, ["ln", "-s", "/native/lib/" + musl,
                                    musl_link])
        pmb.helpers.run.root(args, ["ln", "-sf", "/native/bin/busybox", "/usr/local/bin/gzip"])

def remove_mnt_pmbootstrap(args: PmbArgs, chroot: Chroot):
    """ Safely remove /mnt/pmbootstrap directories from the chroot, without
        running rm -r as root and potentially removing data inside the
        mountpoint in case it was still mounted (bug in pmbootstrap, or user
        ran pmbootstrap 2x in parallel). This is similar to running 'rm -r -d',
        but we don't assume that the host's rm has the -d flag (busybox does
        not). """
    mnt_dir = chroot / "mnt/pmbootstrap"

    if not mnt_dir.exists():
        return

    for path in list(mnt_dir.glob("*")) + [mnt_dir]:
        pmb.helpers.run.root(args, ["rmdir", path])
