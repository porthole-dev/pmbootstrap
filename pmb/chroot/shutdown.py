# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import socket
from contextlib import closing

import pmb.chroot
from pmb.core.types import PmbArgs
import pmb.helpers.mount
import pmb.install.losetup
import pmb.parse.arch
from pmb.core import Chroot, ChrootType


def kill_adb(args: PmbArgs):
    """
    Kill adb daemon if it's running.
    """
    port = 5038
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            pmb.chroot.root(args, ["adb", "-P", str(port), "kill-server"])


def kill_sccache(args: PmbArgs):
    """
    Kill sccache daemon if it's running. Unlike ccache it automatically spawns
    a daemon when you call it and exits after some time of inactivity.
    """
    port = 4226
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            pmb.chroot.root(args, ["sccache", "--stop-server"])


def shutdown_cryptsetup_device(args: PmbArgs, name: str):
    """
    :param name: cryptsetup device name, usually "pm_crypt" in pmbootstrap
    """
    if not (Chroot.native() / "dev/mapper" / name).exists():
        return
    pmb.chroot.apk.install(args, ["cryptsetup"])
    status = pmb.chroot.root(args, ["cryptsetup", "status", name],
                             output_return=True, check=False)
    if not status:
        logging.warning("WARNING: Failed to run cryptsetup to get the status"
                        " for " + name + ", assuming it is not mounted"
                        " (shutdown fails later if it is)!")
        return

    if status.startswith("/dev/mapper/" + name + " is active."):
        pmb.chroot.root(args, ["cryptsetup", "luksClose", name])
    elif status.startswith("/dev/mapper/" + name + " is inactive."):
        # When "cryptsetup status" fails, the device is not mounted and we
        # have a left over file (#83)
        pmb.chroot.root(args, ["rm", "/dev/mapper/" + name])
    else:
        raise RuntimeError("Failed to parse 'cryptsetup status' output!")


def shutdown(args: PmbArgs, only_install_related=False):
    # Stop daemons
    kill_adb(args)
    kill_sccache(args)

    chroot = Chroot.native()

    # Umount installation-related paths (order is important!)
    pmb.helpers.mount.umount_all(args, chroot / "mnt/install")
    shutdown_cryptsetup_device(args, "pm_crypt")

    # Umount all losetup mounted images
    if pmb.helpers.mount.ismount(chroot / "dev/loop-control"):
        for path_outside in (chroot / "/home/pmos/rootfs").glob("*.img"):
            path = path_outside.relative_to(chroot.path)
            pmb.install.losetup.umount(args, path, auto_init=False)

    # Umount device rootfs and installer chroots
    for chroot_type in [ChrootType.ROOTFS, ChrootType.INSTALLER]:
        chroot = Chroot(chroot_type, args.device)
        if chroot.path.exists():
            pmb.helpers.mount.umount_all(args, chroot.path)

    # Remove "in-pmbootstrap" marker from all chroots. This marker indicates
    # that pmbootstrap has set up all mount points etc. to run programs inside
    # the chroots, but we want it gone afterwards (e.g. when the chroot
    # contents get copied to a rootfs / installer image, or if creating an
    # android recovery zip from its contents).
    for marker in pmb.config.work.glob("chroot_*/in-pmbootstrap"):
        pmb.helpers.run.root(args, ["rm", marker])

    if not only_install_related:
        # Umount all folders inside work dir
        # The folders are explicitly iterated over, so folders symlinked inside
        # work dir get umounted as well (used in test_pkgrel_bump.py, #1595)
        for path in pmb.config.work.glob("*"):
            pmb.helpers.mount.umount_all(args, path)

        # Clean up the rest
        for arch in pmb.config.build_device_architectures:
            if pmb.parse.arch.cpu_emulation_required(arch):
                pmb.chroot.binfmt.unregister(args, arch)
        logging.debug("Shutdown complete")
