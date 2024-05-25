# Copyright 2023 Dylan Van Assche
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import List
from pmb.helpers import logging

from pmb.types import Config
import pmb.helpers.pmaports


def get_groups(config: Config) -> List[str]:
    """ Get all groups to which the user additionally must be added.
        The list of groups are listed in _pmb_groups of the UI and
        UI-extras package.

        :returns: list of groups, e.g. ["feedbackd", "udev"] """
    ret: List[str] = []
    if config.ui == "none":
        return ret

    # UI package
    meta = f"postmarketos-ui-{config.ui}"
    apkbuild = pmb.helpers.pmaports.get(meta)
    groups = apkbuild["_pmb_groups"]
    if groups:
        logging.debug(f"{meta}: install _pmb_groups:"
                      f" {', '.join(groups)}")
        ret += groups

    # UI-extras subpackage
    meta_extras = f"{meta}-extras"
    if config.ui_extras and meta_extras in apkbuild["subpackages"]:
        groups = apkbuild["subpackages"][meta_extras]["_pmb_groups"]
        if groups:
            logging.debug(f"{meta_extras}: install _pmb_groups:"
                          f" {', '.join(groups)}")
            ret += groups

    return ret
