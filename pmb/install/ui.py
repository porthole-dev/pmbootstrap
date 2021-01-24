# Copyright 2021 Dylan Van Assche
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import pmb.helpers.pmaports


def get_recommends(args):
    """ Get all packages listed in _pmb_recommends of the UI and UI-extras
        package, unless running with pmbootstrap install --no-recommends.

        :returns: list of pkgnames, e.g. ["chatty", "gnome-contacts"] """
    ret = []
    if not args.install_recommends or args.ui == "none":
        return ret

    # UI package
    meta = f"postmarketos-ui-{args.ui}"
    apkbuild = pmb.helpers.pmaports.get(args, meta)
    recommends = apkbuild["_pmb_recommends"]
    if recommends:
        logging.debug(f"{meta}: install _pmb_recommends:"
                      f" {', '.join(recommends)}")
        ret += recommends

    # UI-extras subpackage
    meta_extras = f"{meta}-extras"
    if args.ui_extras and meta_extras in apkbuild["subpackages"]:
        recommends = apkbuild["subpackages"][meta_extras]["_pmb_recommends"]
        if recommends:
            logging.debug(f"{meta_extras}: install _pmb_recommends:"
                          f" {', '.join(recommends)}")
            ret += recommends

    return ret


