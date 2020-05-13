# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later


def variables(args, flavor, method):
    _cmdline = args.deviceinfo["kernel_cmdline"]
    if "cmdline" in args and args.cmdline:
        _cmdline = args.cmdline

    flash_pagesize = args.deviceinfo['flash_pagesize']

    if method.startswith("fastboot"):
        _partition_kernel = args.deviceinfo["flash_fastboot_partition_kernel"] or "boot"
        _partition_system = args.deviceinfo["flash_fastboot_partition_system"] or "system"
        _partition_vbmeta = args.deviceinfo["flash_fastboot_partition_vbmeta"] or None
    else:
        _partition_kernel = args.deviceinfo["flash_heimdall_partition_kernel"] or "KERNEL"
        _partition_system = args.deviceinfo["flash_heimdall_partition_system"] or "SYSTEM"
        _partition_vbmeta = args.deviceinfo["flash_heimdall_partition_vbmeta"] or None

    if "partition" in args and args.partition:
        # Only one of operations is done at same time so it doesn't matter sharing the arg
        _partition_kernel = args.partition
        _partition_system = args.partition
        _partition_vbmeta = args.partition

    vars = {
        "$BOOT": "/mnt/rootfs_" + args.device + "/boot",
        "$FLAVOR": flavor if flavor is not None else "",
        "$IMAGE_SPLIT_BOOT": "/home/pmos/rootfs/" + args.device + "-boot.img",
        "$IMAGE_SPLIT_ROOT": "/home/pmos/rootfs/" + args.device + "-root.img",
        "$IMAGE": "/home/pmos/rootfs/" + args.device + ".img",
        "$KERNEL_CMDLINE": _cmdline,
        "$PARTITION_KERNEL": _partition_kernel,
        "$PARTITION_INITFS": args.deviceinfo["flash_heimdall_partition_initfs"] or "RECOVERY",
        "$PARTITION_SYSTEM": _partition_system,
        "$PARTITION_VBMETA": _partition_vbmeta,
        "$FLASH_PAGESIZE": flash_pagesize,
        "$RECOVERY_ZIP": "/mnt/buildroot_" + args.deviceinfo["arch"] +
                         "/var/lib/postmarketos-android-recovery-installer"
                         "/pmos-" + args.device + ".zip",
        "$UUU_SCRIPT": "/mnt/rootfs_" + args.deviceinfo["codename"] +
                       "/usr/share/uuu/flash_script.lst"
    }

    return vars
