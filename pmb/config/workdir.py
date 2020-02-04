# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Save, read, verify workdir state related information in $WORK/workdir.cfg,
    for example the init dates of the chroots. This is not saved in
    pmbootstrap.cfg, because pmbootstrap.cfg is not tied to a specific work
    dir. """
import configparser
import os
import time

import pmb.config


def chroot_save_date(args, suffix):
    """ Save the chroot initialization date in $WORK/workdir.cfg. """
    # Read existing cfg
    cfg = configparser.ConfigParser()
    path = args.work + "/workdir.cfg"
    if os.path.isfile(path):
        cfg.read(path)

    # Set current date for chroot suffix
    key = "chroot-init-dates"
    if key not in cfg:
        cfg[key] = {}
    cfg[key][suffix] = str(int(time.time()))

    # Write back
    with open(path, "w") as handle:
        cfg.write(handle)


def chroots_outdated(args):
    """ Check if init dates from workdir.cfg indicate that any chroot is
        outdated.
        :returns: True if any of the chroots are outdated and should be zapped,
                  False otherwise """
    # Skip if workdir.cfg doesn't exist
    path = args.work + "/workdir.cfg"
    if not os.path.exists(path):
        return False

    cfg = configparser.ConfigParser()
    cfg.read(path)
    key = "chroot-init-dates"
    if key not in cfg:
        return False

    date_outdated = time.time() - pmb.config.chroot_outdated
    for suffix in cfg[key]:
        date_init = int(cfg[key][suffix])
        if date_init <= date_outdated:
            return True
    return False


def clean(args):
    """ Remove obsolete data data from workdir.cfg.
        :returns: None if workdir does not exist,
                  True if config was rewritten,
                  False if config did not change """
    # Skip if workdir.cfg doesn't exist
    path = args.work + "/workdir.cfg"
    if not os.path.exists(path):
        return None

    # Read
    cfg = configparser.ConfigParser()
    cfg.read(path)

    # Remove entries for deleted chroots
    key = "chroot-init-dates"
    changed = False
    if key in cfg:
        for suffix in cfg[key]:
            path_suffix = args.work + "/chroot_" + suffix
            if os.path.exists(path_suffix):
                continue
            changed = True
            del cfg[key][suffix]

    # Write back
    if changed:
        with open(path, "w") as handle:
            cfg.write(handle)

    return changed
