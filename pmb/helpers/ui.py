# Copyright 2020 Clayton Craft
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import glob
import pmb.parse


def list(args):
    """
    Get all UIs, for which aports are available with their description.

    :returns: [("none", "No graphical..."), ("weston", "Wayland reference...")]
    """
    ret = [("none", "No graphical environment")]
    for path in sorted(glob.glob(args.aports + "/main/postmarketos-ui-*")):
        apkbuild = pmb.parse.apkbuild(args, path + "/APKBUILD")
        ui = os.path.basename(path).split("-", 2)[2]
        ret.append((ui, apkbuild["pkgdesc"]))
    return ret
