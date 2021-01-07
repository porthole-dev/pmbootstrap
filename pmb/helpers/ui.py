# Copyright 2021 Clayton Craft
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import glob
import pmb.parse


def list(args, arch):
    """
    Get all UIs, for which aports are available with their description.

    :param arch: device architecture, for which the UIs must be available
    :returns: [("none", "No graphical..."), ("weston", "Wayland reference...")]
    """
    ret = [("none", "No graphical environment")]
    for path in sorted(glob.glob(args.aports + "/main/postmarketos-ui-*")):
        apkbuild = pmb.parse.apkbuild(args, path + "/APKBUILD")
        ui = os.path.basename(path).split("-", 2)[2]
        if pmb.helpers.package.check_arch(args, apkbuild["pkgname"], arch):
            ret.append((ui, apkbuild["pkgdesc"]))
    return ret
