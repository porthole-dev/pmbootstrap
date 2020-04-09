# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
import logging
import os

import pmb.config
import pmb.helpers.git


def check_legacy_folder():
    # Existing pmbootstrap/aports must be a symlink
    link = pmb.config.pmb_src + "/aports"
    if os.path.exists(link) and not os.path.islink(link):
        raise RuntimeError("The path '" + link + "' should be a"
                           " symlink pointing to the new pmaports"
                           " repository, which was split from the"
                           " pmbootstrap repository (#383). Consider"
                           " making a backup of that folder, then delete"
                           " it and run 'pmbootstrap init' again to let"
                           " pmbootstrap clone the pmaports repository and"
                           " set up the symlink.")


def clone(args):
    # Explain sudo-usage before using it the first time
    logging.info("pmbootstrap does everything in Alpine Linux chroots, so your"
                 " host system does not get modified. In order to work with"
                 " these chroots, pmbootstrap calls 'sudo' internally. To see"
                 " the commands it runs, you can run 'pmbootstrap log' in a"
                 " second terminal.")
    logging.info("Setting up the native chroot and cloning the package build"
                 " recipes (pmaports)...")

    # Set up the native chroot and clone pmaports
    pmb.helpers.git.clone(args, "pmaports", False)


def symlink(args):
    # Create the symlink
    # This won't work when pmbootstrap was installed system wide, but that's
    # okay since the symlink is only intended to make the migration to the
    # pmaports repository easier.
    link = pmb.config.pmb_src + "/aports"
    try:
        os.symlink(args.aports, link)
        logging.info("NOTE: pmaports path: " + link)
    except:
        logging.info("NOTE: pmaports path: " + args.aports)


def check_version_pmaports(real):
    # Compare versions
    min = pmb.config.pmaports_min_version
    if pmb.parse.version.compare(real, min) >= 0:
        return

    # Outated error
    logging.info("NOTE: your pmaports folder has version " + real + ", but" +
                 " version " + min + " is required.")
    raise RuntimeError("Run 'pmbootstrap pull' to update your pmaports.")


def check_version_pmbootstrap(min):
    # Compare versions
    real = pmb.config.version
    if pmb.parse.version.compare(real, min) >= 0:
        return

    # Show versions
    logging.info("NOTE: you are using pmbootstrap version " + real + ", but" +
                 " version " + min + " is required.")

    # Error for git clone
    pmb_src = pmb.config.pmb_src
    if os.path.exists(pmb_src + "/.git"):
        raise RuntimeError("Please update your local pmbootstrap repository."
                           " Usually with: 'git -C \"" + pmb_src + "\" pull'")

    # Error for package manager installation
    raise RuntimeError("Please update your pmbootstrap version (with your"
                       " distribution's package manager, or with pip, "
                       " depending on how you have installed it). If that is"
                       " not possible, consider cloning the latest version"
                       " of pmbootstrap from git.")


def read_config(args):
    """ Read and verify pmaports.cfg. """
    # Try cache first
    cache_key = "pmb.config.pmaports.read_config"
    if args.cache[cache_key]:
        return args.cache[cache_key]

    # Migration message
    if not os.path.exists(args.aports):
        raise RuntimeError("We have split the aports repository from the"
                           " pmbootstrap repository (#383). Please run"
                           " 'pmbootstrap init' again to clone it.")

    # Require the config
    path_cfg = args.aports + "/pmaports.cfg"
    if not os.path.exists(path_cfg):
        raise RuntimeError("Invalid pmaports repository, could not find the"
                           " config: " + path_cfg)

    # Load the config
    cfg = configparser.ConfigParser()
    cfg.read(path_cfg)
    ret = cfg["pmaports"]

    # Version checks
    check_version_pmaports(ret["version"])
    check_version_pmbootstrap(ret["pmbootstrap_min_version"])

    # Cache and return
    args.cache[cache_key] = ret
    return ret


def init(args):
    check_legacy_folder()
    if not os.path.exists(args.aports):
        clone(args)
    symlink(args)
    read_config(args)


def switch_to_channel_branch(args, channel_new):
    """ Checkout the channel's branch in pmaports.git.
        :channel_new: channel name (e.g. "edge", "stable")
        :returns: True if another branch was checked out, False otherwise """
    # Check current pmaports branch channel
    channel_current = read_config(args)["channel"]
    if channel_current == channel_new:
        return False

    # List current and new branches/channels
    channels_cfg = pmb.helpers.git.parse_channels_cfg(args)
    branch_new = channels_cfg["channels"][channel_new]["branch_pmaports"]
    branch_current = pmb.helpers.git.rev_parse(args, args.aports,
                                               extra_args=["--abbrev-ref"])
    logging.info(f"Currently checked out branch '{branch_current}' of"
                 f" pmaports.git is on channel '{channel_current}'.")
    logging.info(f"Switching to branch '{branch_new}' on channel"
                 f" '{channel_new}'...")

    # Attempt to switch branch (git gives a nice error message, mentioning
    # which files need to be committed/stashed, so just pass it through)
    if pmb.helpers.run.user(args, ["git", "checkout", branch_new],
                            args.aports, "interactive", check=False):
        raise RuntimeError("Failed to switch branch. Go to your pmaports and"
                           " fix what git complained about, then try again: "
                           f"{args.aports}")

    # Invalidate all caches
    pmb.helpers.args.add_cache(args)

    # Verify pmaports.cfg on new branch
    read_config(args)
    return True
