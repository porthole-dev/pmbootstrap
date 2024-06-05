# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional
import pmb.config.pmaports
from pmb.core.context import get_context
from pmb.types import PmbArgs


def variables(args: PmbArgs, flavor, method):
    device = get_context().config.device
    deviceinfo = pmb.parse.deviceinfo()
    _cmdline = deviceinfo["kernel_cmdline"] or ""
    if "cmdline" in args and args.cmdline:
        _cmdline = args.cmdline

    flash_pagesize = deviceinfo['flash_pagesize']

    # TODO Remove _partition_system deviceinfo support once pmaports has been
    # updated and minimum pmbootstrap version bumped.
    # See also https://gitlab.com/postmarketOS/pmbootstrap/-/issues/2243

    _partition_kernel: Optional[str]
    _partition_rootfs: Optional[str]

    if method.startswith("fastboot"):
        _partition_kernel = deviceinfo["flash_fastboot_partition_kernel"]\
            or "boot"
        _partition_rootfs = deviceinfo["flash_fastboot_partition_rootfs"]\
            or deviceinfo["flash_fastboot_partition_system"] or "userdata"
        _partition_vbmeta = deviceinfo["flash_fastboot_partition_vbmeta"]\
            or None
        _partition_dtbo = deviceinfo["flash_fastboot_partition_dtbo"]\
            or None
    # Require that the partitions are specified in deviceinfo for now
    elif method.startswith("rkdeveloptool"):
        _partition_kernel = deviceinfo["flash_rk_partition_kernel"]\
            or None
        _partition_rootfs = deviceinfo["flash_rk_partition_rootfs"]\
            or deviceinfo["flash_rk_partition_system"] or None
        _partition_vbmeta = None
        _partition_dtbo = None
    elif method.startswith("mtkclient"):
        _partition_kernel = deviceinfo["flash_mtkclient_partition_kernel"]\
            or "boot"
        _partition_rootfs = deviceinfo["flash_mtkclient_partition_rootfs"]\
            or "userdata"
        _partition_vbmeta = deviceinfo["flash_mtkclient_partition_vbmeta"]\
            or None
        _partition_dtbo = deviceinfo["flash_mtkclient_partition_dtbo"]\
            or None
    else:
        _partition_kernel = deviceinfo["flash_heimdall_partition_kernel"]\
            or "KERNEL"
        _partition_rootfs = deviceinfo["flash_heimdall_partition_rootfs"]\
            or deviceinfo["flash_heimdall_partition_system"] or "SYSTEM"
        _partition_vbmeta = deviceinfo["flash_heimdall_partition_vbmeta"]\
            or None
        _partition_dtbo = deviceinfo["flash_heimdall_partition_dtbo"]\
            or None

    if "partition" in args and args.partition:
        # Only one operation is done at same time so it doesn't matter
        # sharing the arg
        _partition_kernel = args.partition
        _partition_rootfs = args.partition
        _partition_vbmeta = args.partition
        _partition_dtbo = args.partition

    _dtb = ""
    if deviceinfo["append_dtb"] == "true":
        _dtb = "-dtb"

    _no_reboot = ""
    if getattr(args, 'no_reboot', False):
        _no_reboot = "--no-reboot"

    _resume = ""
    if getattr(args,'resume', False):
        _resume = "--resume"

    vars = {
        "$BOOT": "/mnt/rootfs_" + device + "/boot",
        "$DTB": _dtb,
        "$IMAGE_SPLIT_BOOT": "/home/pmos/rootfs/" + device + "-boot.img",
        "$IMAGE_SPLIT_ROOT": "/home/pmos/rootfs/" + device + "-root.img",
        "$IMAGE": "/home/pmos/rootfs/" + device + ".img",
        "$KERNEL_CMDLINE": _cmdline,
        "$PARTITION_KERNEL": _partition_kernel,
        "$PARTITION_INITFS": deviceinfo[
            "flash_heimdall_partition_initfs"] or "RECOVERY",
        "$PARTITION_ROOTFS": _partition_rootfs,
        "$PARTITION_VBMETA": _partition_vbmeta,
        "$PARTITION_DTBO": _partition_dtbo,
        "$FLASH_PAGESIZE": flash_pagesize,
        "$RECOVERY_ZIP": "/mnt/buildroot_" + deviceinfo["arch"] +
                         "/var/lib/postmarketos-android-recovery-installer"
                         "/pmos-" + device + ".zip",
        "$UUU_SCRIPT": "/mnt/rootfs_" + deviceinfo["codename"] +
                       "/usr/share/uuu/flash_script.lst",
        "$NO_REBOOT": _no_reboot,
        "$RESUME": _resume
    }

    # Backwards compatibility with old mkinitfs (pma#660)
    pmaports_cfg = pmb.config.pmaports.read_config()
    if pmaports_cfg.get("supported_mkinitfs_without_flavors", False):
        vars["$FLAVOR"] = ""
    else:
        vars["$FLAVOR"] = f"-{flavor}" if flavor is not None else "-"

    return vars
