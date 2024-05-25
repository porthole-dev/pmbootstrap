# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.chroot.apk
import pmb.config
import pmb.config.pmaports
from pmb.types import PmbArgs
import pmb.helpers.mount
from pmb.helpers.mount import mount_device_rootfs
from pmb.core import Chroot, ChrootType


def install_depends(args: PmbArgs):
    if hasattr(args, 'flash_method'):
        method = args.flash_method or args.deviceinfo["flash_method"]
    else:
        method = args.deviceinfo["flash_method"]

    if method not in pmb.config.flashers:
        raise RuntimeError(f"Flash method {method} is not supported by the"
                           " current configuration. However, adding a new"
                           " flash method is not that hard, when the flashing"
                           " application already exists.\n"
                           "Make sure, it is packaged for Alpine Linux, or"
                           " package it yourself, and then add it to"
                           " pmb/config/__init__.py.")
    depends = pmb.config.flashers[method]["depends"]

    # Depends for some flash methods may be different for various pmaports
    # branches, so read them from pmaports.cfg.
    if method == "fastboot":
        pmaports_cfg = pmb.config.pmaports.read_config()
        depends = pmaports_cfg.get("supported_fastboot_depends",
                                   "android-tools,avbtool").split(",")
    elif method == "heimdall-bootimg":
        pmaports_cfg = pmb.config.pmaports.read_config()
        depends = pmaports_cfg.get("supported_heimdall_depends",
                                   "heimdall,avbtool").split(",")
    elif method == "mtkclient":
        pmaports_cfg = pmb.config.pmaports.read_config()
        depends = pmaports_cfg.get("supported_mtkclient_depends",
                                   "mtkclient,android-tools").split(",")

    pmb.chroot.apk.install(depends, Chroot.native())


def init(args: PmbArgs):
    install_depends(args)

    # Mount folders from host system
    for folder in pmb.config.flash_mount_bind:
        pmb.helpers.mount.bind(folder, Chroot.native() / folder)

    # Mount device chroot inside native chroot (required for kernel/ramdisk)
    mount_device_rootfs(args, Chroot(ChrootType.ROOTFS, args.device))
