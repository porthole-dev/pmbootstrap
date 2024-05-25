# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
from pathlib import Path
from pmb.core import get_context
from pmb.helpers import logging
import os
import sys

import pmb.config
from pmb.types import PmbArgs
import pmb.helpers.git
import pmb.helpers.pmaports
import pmb.parse.version


def clone():
    logging.info("Setting up the native chroot and cloning the package build"
                 " recipes (pmaports)...")

    # Set up the native chroot and clone pmaports
    pmb.helpers.git.clone("pmaports")


def check_version_pmaports(real):
    # Compare versions
    min = pmb.config.pmaports_min_version
    if pmb.parse.version.compare(real, min) >= 0:
        return

    # Outated error
    logging.info("NOTE: your pmaports folder has version " + real + ", but" +
                 " version " + min + " is required.")
    raise RuntimeError("Run 'pmbootstrap pull' to update your pmaports.")


def check_version_pmbootstrap(min_ver):
    # Compare versions
    real = pmb.__version__
    if pmb.parse.version.compare(real, min_ver) >= 0:
        return

    # Show versions
    logging.info(f"NOTE: you are using pmbootstrap version {real}, but"
                 f" version {min_ver} is required.")

    # Error for git clone
    pmb_src = pmb.config.pmb_src
    if os.path.exists(pmb_src / ".git"):
        raise RuntimeError("Please update your local pmbootstrap repository."
                          f" Usually with: 'git -C \"{pmb_src}\" pull'")

    # Error for package manager installation
    raise RuntimeError("Please update your pmbootstrap version (with your"
                       " distribution's package manager, or with pip, "
                       " depending on how you have installed it). If that is"
                       " not possible, consider cloning the latest version"
                       " of pmbootstrap from git.")


def read_config_repos():
    """ Read the sections starting with "repo:" from pmaports.cfg. """
    # Try cache first
    cache_key = "pmb.config.pmaports.read_config_repos"
    if pmb.helpers.other.cache[cache_key]:
        return pmb.helpers.other.cache[cache_key]

    cfg = configparser.ConfigParser()
    cfg.read(f"{get_context().config.aports}/pmaports.cfg")

    ret = {}
    for section in cfg.keys():
        if not section.startswith("repo:"):
            continue
        repo = section.split("repo:", 1)[1]
        ret[repo] = cfg[section]

    # Cache and return
    pmb.helpers.other.cache[cache_key] = ret
    return ret


def read_config():
    """Read and verify pmaports.cfg."""
    # Try cache first
    cache_key = "pmb.config.pmaports.read_config"
    if pmb.helpers.other.cache[cache_key]:
        return pmb.helpers.other.cache[cache_key]

    aports = get_context().config.aports
    # Migration message
    if not os.path.exists(aports):
        logging.error(f"ERROR: pmaports dir not found: {aports}")
        logging.error("Did you run 'pmbootstrap init'?")
        sys.exit(1)

    # Require the config
    path_cfg = aports / "pmaports.cfg"
    if not os.path.exists(path_cfg):
        raise RuntimeError("Invalid pmaports repository, could not find the"
                          f" config: {path_cfg}")

    # Load the config
    cfg = configparser.ConfigParser()
    cfg.read(path_cfg)
    ret = cfg["pmaports"]

    # Version checks
    check_version_pmaports(ret["version"])
    check_version_pmbootstrap(ret["pmbootstrap_min_version"])

    # Translate legacy channel names
    ret["channel"] = pmb.helpers.pmaports.get_channel_new(ret["channel"])

    # Cache and return
    pmb.helpers.other.cache[cache_key] = ret
    return ret


def read_config_channel():
    """Get the properties of the currently active channel in pmaports.git.

    As specified in channels.cfg (https://postmarketos.org/channels.cfg).

    :returns: {"description: ...,
               "branch_pmaports": ...,
               "branch_aports": ...,
               "mirrordir_alpine": ...}

    """
    aports = get_context().config.aports
    channel = read_config()["channel"]
    channels_cfg = pmb.helpers.git.parse_channels_cfg(aports)

    if channel in channels_cfg["channels"]:
        return channels_cfg["channels"][channel]

    # Channel not in channels.cfg, try to be helpful
    branch = pmb.helpers.git.rev_parse(aports,
                                       extra_args=["--abbrev-ref"])
    branches_official = pmb.helpers.git.get_branches_official(aports)
    branches_official = ", ".join(branches_official)
    remote = pmb.helpers.git.get_upstream_remote(aports)
    logging.info("NOTE: fix the error by rebasing or cherry picking relevant"
                 " commits from this branch onto a branch that is on a"
                 f" supported channel: {branches_official}")
    logging.info("NOTE: as workaround, you may pass --config-channels with a"
                 " custom channels.cfg. Reference:"
                 " https://postmarketos.org/channels.cfg")
    raise RuntimeError(f"Current branch '{branch}' of pmaports.git is on"
                       f" channel '{channel}', but this channel was not"
                       f" found in channels.cfg (of {remote}/master"
                       " branch). Looks like a very old branch.")


def init():
    if not os.path.exists(get_context().config.aports):
        clone()
    read_config()


def switch_to_channel_branch(args: PmbArgs, channel_new):
    """Checkout the channel's branch in pmaports.git.

    :channel_new: channel name (e.g. "edge", "v21.03")

    :returns: True if another branch was checked out, False otherwise
    """
    # Check current pmaports branch channel
    channel_current = read_config()["channel"]
    if channel_current == channel_new:
        return False

    aports = get_context().config.aports
    # List current and new branches/channels
    channels_cfg = pmb.helpers.git.parse_channels_cfg(aports)
    branch_new = channels_cfg["channels"][channel_new]["branch_pmaports"]
    branch_current = pmb.helpers.git.rev_parse(aports,
                                               extra_args=["--abbrev-ref"])
    logging.info(f"Currently checked out branch '{branch_current}' of"
                 f" pmaports.git is on channel '{channel_current}'.")
    logging.info(f"Switching to branch '{branch_new}' on channel"
                 f" '{channel_new}'...")

    # Make sure we don't have mounts related to the old channel
    pmb.chroot.shutdown(args)

    # Attempt to switch branch (git gives a nice error message, mentioning
    # which files need to be committed/stashed, so just pass it through)
    if pmb.helpers.run.user(["git", "checkout", branch_new],
                            aports, "interactive", check=False):
        raise RuntimeError("Failed to switch branch. Go to your pmaports and"
                           " fix what git complained about, then try again: "
                           f"{aports}")

    # Verify pmaports.cfg on new branch
    read_config()
    return True


def install_githooks():
    aports = get_context().config.aports
    hooks_dir = aports / ".githooks"
    if not hooks_dir.exists():
        logging.info("No .githooks dir found")
        return
    for h in os.listdir(hooks_dir):
        src = os.path.join(hooks_dir, h)
        # Use git default hooks dir so users can ignore our hooks
        # if they dislike them by setting "core.hooksPath" git config
        dst = aports / ".git/hooks" / h
        if pmb.helpers.run.user(["cp", src, dst], check=False):
            logging.warning(f"WARNING: Copying git hook failed: {dst}")
