# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Save, read, verify workdir state related information in $WORK/workdir.cfg,
    for example the init dates of the chroots. This is not saved in
    pmbootstrap.cfg, because pmbootstrap.cfg is not tied to a specific work
    dir. """
import configparser
import os
import time
from typing import Optional

import pmb.config
import pmb.config.pmaports
from pmb.core import Chroot
from pmb.core.context import get_context
from pmb.helpers import logging


def chroot_save_init(suffix: Chroot):
    """Save the chroot initialization data in $WORK/workdir.cfg."""
    # Read existing cfg
    cfg = configparser.ConfigParser()
    path = get_context().config.work / "workdir.cfg"
    if os.path.isfile(path):
        cfg.read(path)

    # Create sections
    for key in ["chroot-init-dates", "chroot-channels"]:
        if key not in cfg:
            cfg[key] = {}

    # Update sections
    channel = pmb.config.pmaports.read_config()["channel"]
    cfg["chroot-channels"][str(suffix)] = channel
    cfg["chroot-init-dates"][str(suffix)] = str(int(time.time()))

    # Write back
    with open(path, "w") as handle:
        cfg.write(handle)


def chroots_outdated(chroot: Optional[Chroot]=None):
    """Check if init dates from workdir.cfg indicate that any chroot is
    outdated.

    :param suffix: only check a specific chroot suffix

    :returns: True if any of the chroots are outdated and should be zapped,
              False otherwise
    """
    # Skip if workdir.cfg doesn't exist
    path = get_context().config.work / "workdir.cfg"
    if not os.path.exists(path):
        return False

    cfg = configparser.ConfigParser()
    cfg.read(path)
    key = "chroot-init-dates"
    if key not in cfg:
        return False

    date_outdated = time.time() - pmb.config.chroot_outdated
    for cfg_suffix in cfg[key]:
        if chroot and cfg_suffix != str(chroot):
            continue
        date_init = int(cfg[key][cfg_suffix])
        if date_init <= date_outdated:
            return True
    return False


def chroot_check_channel(chroot: Chroot) -> bool:
    """Check the chroot channel against the current channel. Returns
    True if the chroot should be zapped (both that it needs zapping and
    the user has auto_zap_misconfigured_chroots enabled), False otherwise."""
    config = get_context().config
    path = config.work / "workdir.cfg"
    msg_again = "Run 'pmbootstrap zap' to delete your chroots and try again." \
        " To do this automatically, run 'pmbootstrap config" \
        " auto_zap_misconfigured_chroots yes'."
    msg_unknown = ("Could not figure out on which release channel the"
                   f" '{chroot}' chroot is.")
    if not os.path.exists(path):
        raise RuntimeError(f"{msg_unknown} {msg_again}")

    cfg = configparser.ConfigParser()
    cfg.read(path)
    key = "chroot-channels"
    if key not in cfg or str(chroot) not in cfg[key]:
        raise RuntimeError(f"{msg_unknown} {msg_again}")

    channel = pmb.config.pmaports.read_config()["channel"]
    channel_cfg = cfg[key][str(chroot)]
    msg = f"Chroot '{chroot}' is for the '{channel_cfg}' channel," \
          f" but you are on the '{channel}' channel."

    if channel != channel_cfg:
        if config.auto_zap_misconfigured_chroots.enabled():
            if config.auto_zap_misconfigured_chroots.noisy():
                logging.info(msg)
                logging.info("Automatically zapping since"
                             " auto_zap_misconfigured_chroots is enabled.")
                logging.info("NOTE: You can silence this message with 'pmbootstrap"
                             " config auto_zap_misconfigured_chroots silently'")
            else:
                logging.debug(f"{msg} Zapping chroot.")
            return True
        raise RuntimeError(f"{msg} {msg_again}")

    return False


def clean():
    """Remove obsolete data data from workdir.cfg.

    :returns: None if workdir does not exist,
        True if config was rewritten,
        False if config did not change
    """
    # Skip if workdir.cfg doesn't exist
    path = get_context().config.work / "workdir.cfg"
    if not os.path.exists(path):
        return None

    # Read
    cfg = configparser.ConfigParser()
    cfg.read(path)

    # Remove entries for deleted chroots
    changed = False
    for key in ["chroot-init-dates", "chroot-channels"]:
        if key not in cfg:
            continue
        for suffix_str in cfg[key]:
            suffix = Chroot.from_str(suffix_str)
            if suffix.path.exists():
                continue
            changed = True
            del cfg[key][suffix_str]

    # Write back
    if changed:
        with path.open("w") as handle:
            cfg.write(handle)

    return changed
