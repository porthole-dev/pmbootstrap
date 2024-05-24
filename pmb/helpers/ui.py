# Copyright 2023 Clayton Craft
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import glob
from pmb.core import get_context
from pmb.core.types import PmbArgs
import pmb.helpers.pmaports
import pmb.helpers.package
import pmb.parse


def list_ui(args: PmbArgs, arch):
    """Get all UIs, for which aports are available with their description.

    :param arch: device architecture, for which the UIs must be available
    :returns: [("none", "No graphical..."), ("weston", "Wayland reference...")]
    """
    ret = [("none", "Bare minimum OS image for testing and manual"
                    " customization. The \"console\" UI should be selected if"
                    " a graphical UI is not desired.")]
    context = get_context()  # noqa: F821
    for path in sorted(context.aports.glob("main/postmarketos-ui-*")):
        apkbuild = pmb.parse.apkbuild(path)
        ui = os.path.basename(path).split("-", 2)[2]
        if pmb.helpers.package.check_arch(args, apkbuild["pkgname"], arch):
            ret.append((ui, apkbuild["pkgdesc"]))
    return ret


def check_option(args: PmbArgs, ui, option):
    """
    Check if an option, such as pmb:systemd, is inside an UI's APKBUILD.
    """
    pkgname = f"postmarketos-ui-{ui}"
    apkbuild = pmb.helpers.pmaports.get(args, pkgname, subpackages=False)
    return option in apkbuild["options"]
