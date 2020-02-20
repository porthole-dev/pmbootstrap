# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import glob
import pmb.parse


def list_codenames(args, vendor=None):
    """
    Get all devices, for which aports are available
    :param vendor: vendor name to choose devices from, or None for all vendors
    :returns: ["first-device", "second-device", ...]
    """
    ret = []
    for path in glob.glob(args.aports + "/device/device-*"):
        device = os.path.basename(path).split("-", 1)[1]
        if (vendor is None) or device.startswith(vendor + '-'):
            ret.append(device)
    return ret


def list_vendors(args):
    """
    Get all device vendors, for which aports are available
    :returns: {"vendor1", "vendor2", ...}
    """
    ret = set()
    for path in glob.glob(args.aports + "/device/device-*"):
        vendor = os.path.basename(path).split("-", 2)[1]
        ret.add(vendor)
    return ret


def list_apkbuilds(args):
    """
    :returns: { "first-device": {"pkgname": ..., "pkgver": ...}, ... }
    """
    ret = {}
    for device in list_codenames(args):
        apkbuild_path = args.aports + "/device/device-" + device + "/APKBUILD"
        ret[device] = pmb.parse.apkbuild(args, apkbuild_path)
    return ret


def list_deviceinfos(args):
    """
    :returns: { "first-device": {"name": ..., "screen_width": ...}, ... }
    """
    ret = {}
    for device in list_codenames(args):
        ret[device] = pmb.parse.deviceinfo(args, device)
    return ret
