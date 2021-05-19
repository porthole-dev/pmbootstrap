# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os

import pmb.config
import pmb.flasher
import pmb.install
import pmb.chroot.apk
import pmb.chroot.initfs
import pmb.chroot.other
import pmb.helpers.frontend
import pmb.parse.kconfig


def kernel(args):
    # Rebuild the initramfs, just to make sure (see #69)
    flavor = pmb.helpers.frontend._parse_flavor(args, args.autoinstall)
    if args.autoinstall:
        pmb.chroot.initfs.build(args, flavor, "rootfs_" + args.device)

    # Check kernel config
    pmb.parse.kconfig.check(args, flavor)

    # Generate the paths and run the flasher
    if args.action_flasher == "boot":
        logging.info("(native) boot " + flavor + " kernel")
        pmb.flasher.run(args, "boot", flavor)
    else:
        logging.info("(native) flash kernel " + flavor)
        pmb.flasher.run(args, "flash_kernel", flavor)
    logging.info("You will get an IP automatically assigned to your "
                 "USB interface shortly.")
    logging.info("Then you can connect to your device using ssh after pmOS has"
                 " booted:")
    logging.info("ssh {}@{}".format(args.user, pmb.config.default_ip))
    logging.info("NOTE: If you enabled full disk encryption, you should make"
                 " sure that osk-sdl has been properly configured for your"
                 " device")


def list_flavors(args):
    suffix = "rootfs_" + args.device
    logging.info("(" + suffix + ") installed kernel flavors:")
    for flavor in pmb.chroot.other.kernel_flavors_installed(args, suffix):
        logging.info("* " + flavor)


def rootfs(args):
    method = args.flash_method or args.deviceinfo["flash_method"]

    # Generate rootfs, install flasher
    suffix = ".img"
    if pmb.config.flashers.get(method, {}).get("split", False):
        suffix = "-root.img"

    img_path = f"{args.work}/chroot_native/home/pmos/rootfs/{args.device}"\
               f"{suffix}"
    if not os.path.exists(img_path):
        raise RuntimeError("The rootfs has not been generated yet, please run"
                           " 'pmbootstrap install' first.")

    # Do not flash if using fastboot & image is too large
    if method.startswith("fastboot") \
            and args.deviceinfo["flash_fastboot_max_size"]:
        img_size = os.path.getsize(img_path) / 1024**2
        max_size = int(args.deviceinfo["flash_fastboot_max_size"])
        if img_size > max_size:
            raise RuntimeError("The rootfs is too large for fastboot to"
                               " flash.")

    # Run the flasher
    logging.info("(native) flash rootfs image")
    pmb.flasher.run(args, "flash_rootfs")


def flash_vbmeta(args):
    logging.info("(native) flash vbmeta.img with verity disabled flag")
    pmb.flasher.run(args, "flash_vbmeta")


def list_devices(args):
    pmb.flasher.run(args, "list_devices")


def sideload(args):
    method = args.flash_method or args.deviceinfo["flash_method"]
    cfg = pmb.config.flashers[method]

    # Install depends
    pmb.chroot.apk.install(args, cfg["depends"])

    # Mount the buildroot
    suffix = "buildroot_" + args.deviceinfo["arch"]
    mountpoint = "/mnt/" + suffix
    pmb.helpers.mount.bind(args, args.work + "/chroot_" + suffix,
                           args.work + "/chroot_native/" + mountpoint)

    # Missing recovery zip error
    zip_path = ("/var/lib/postmarketos-android-recovery-installer/pmos-" +
                args.device + ".zip")
    if not os.path.exists(args.work + "/chroot_native" + mountpoint +
                          zip_path):
        raise RuntimeError("The recovery zip has not been generated yet,"
                           " please run 'pmbootstrap install' with the"
                           " '--android-recovery-zip' parameter first!")

    pmb.flasher.run(args, "sideload")


def frontend(args):
    action = args.action_flasher
    method = args.flash_method or args.deviceinfo["flash_method"]

    # Legacy alias
    if action == "flash_system":
        action = "flash_rootfs"

    if method == "none" and action in ["boot", "flash_kernel", "flash_rootfs"]:
        logging.info("This device doesn't support any flash method.")
        return

    if action in ["boot", "flash_kernel"]:
        kernel(args)
    if action == "flash_rootfs":
        rootfs(args)
    if action == "flash_vbmeta":
        flash_vbmeta(args)
    if action == "list_flavors":
        list_flavors(args)
    if action == "list_devices":
        list_devices(args)
    if action == "sideload":
        sideload(args)
