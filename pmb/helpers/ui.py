# Copyright 2023 Clayton Craft
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pmb.core.pkgrepo import pkgrepo_iglob
import pmb.helpers.pmaports
import pmb.helpers.package
import pmb.parse


def list_ui(arch):
    """Get all UIs, for which aports are available with their description.

    :param arch: device architecture, for which the UIs must be available
    :returns: [("none", "No graphical..."), ("weston", "Wayland reference...")]
    """
    ret = [
        (
            "none",
            "Bare minimum OS image for testing and manual"
            ' customization. The "console" UI should be selected if'
            " a graphical UI is not desired.",
        )
    ]
    for path in sorted(pkgrepo_iglob("main/postmarketos-ui-*")):
        apkbuild = pmb.parse.apkbuild(path)
        ui = os.path.basename(path).split("-", 2)[2]
        if pmb.helpers.package.check_arch(apkbuild["pkgname"], arch):
            ret.append((ui, apkbuild["pkgdesc"]))
    return ret


def check_option(ui, option, skip_extra_repos=False):
    """
    Check if an option, such as pmb:systemd, is inside an UI's APKBUILD.
    """
    if ui == "none":
        # Users can select "none" as UI in "pmbootstrap init", which does not
        # have a UI package.
        return False

    pkgname = f"postmarketos-ui-{ui}"
    apkbuild = pmb.helpers.pmaports.get(
        pkgname, subpackages=False, skip_extra_repos=skip_extra_repos
    )
    return option in apkbuild["options"]
