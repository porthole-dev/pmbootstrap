# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
from pathlib import Path
from typing import Dict
from pmb.helpers import logging
import os
from pathlib import Path

import pmb.build
import pmb.chroot.apk
import pmb.config
from pmb.core.types import PmbArgs
import pmb.helpers.pmaports
import pmb.helpers.run


def get_path(args: PmbArgs, name_repo):
    """Get the path to the repository.

    The path is either the default one in the work dir, or a user-specified one in args.

    :returns: full path to repository
    """
    if name_repo == "pmaports":
        return args.aports
    return pmb.config.work / "cache_git" / name_repo


def clone(args: PmbArgs, name_repo):
    """Clone a git repository to $WORK/cache_git/$name_repo.

    (or to the overridden path set in args, as with ``pmbootstrap --aports``).

    :param name_repo: short alias used for the repository name, from pmb.config.git_repos
        (e.g. "aports_upstream", "pmaports")
    """
    # Check for repo name in the config
    if name_repo not in pmb.config.git_repos:
        raise ValueError("No git repository configured for " + name_repo)

    path = get_path(args, name_repo)
    if not os.path.exists(path):
        # Build git command
        url = pmb.config.git_repos[name_repo][0]
        command = ["git", "clone"]
        command += [url, path]

        # Create parent dir and clone
        logging.info("Clone git repository: " + url)
        os.makedirs(pmb.config.work / "cache_git", exist_ok=True)
        pmb.helpers.run.user(command, output="stdout")

    # FETCH_HEAD does not exist after initial clone. Create it, so
    # is_outdated() can use it.
    fetch_head = path + "/.git/FETCH_HEAD"
    if not os.path.exists(fetch_head):
        open(fetch_head, "w").close()


def rev_parse(args: PmbArgs, path, revision="HEAD", extra_args: list = []):
    """Run "git rev-parse" in a specific repository dir.

    :param path: to the git repository
    :param extra_args: additional arguments for ``git rev-parse``. Pass
        ``--abbrev-ref`` to get the branch instead of the commit, if possible.
    :returns: commit string like "90cd0ad84d390897efdcf881c0315747a4f3a966"
        or (with ``--abbrev-ref``): the branch name, e.g. "master"
    """
    command = ["git", "rev-parse"] + extra_args + [revision]
    rev = pmb.helpers.run.user_output(command, path)
    return rev.rstrip()


def can_fast_forward(args: PmbArgs, path, branch_upstream, branch="HEAD"):
    command = ["git", "merge-base", "--is-ancestor", branch, branch_upstream]
    ret = pmb.helpers.run.user(command, path, check=False)
    if ret == 0:
        return True
    elif ret == 1:
        return False
    else:
        raise RuntimeError("Unexpected exit code from git: " + str(ret))


def clean_worktree(args: PmbArgs, path):
    """Check if there are not any modified files in the git dir."""
    command = ["git", "status", "--porcelain"]
    return pmb.helpers.run.user_output(command, path) == ""


def get_upstream_remote(args: PmbArgs, name_repo):
    """Find the remote, which matches the git URL from the config.

    Usually "origin", but the user may have set up their git repository differently.
    """
    urls = pmb.config.git_repos[name_repo]
    path = get_path(args, name_repo)
    command = ["git", "remote", "-v"]
    output = pmb.helpers.run.user_output(command, path)
    for line in output.split("\n"):
        if any(u in line for u in urls):
            return line.split("\t", 1)[0]
    raise RuntimeError("{}: could not find remote name for any URL '{}' in git"
                       " repository: {}".format(name_repo, urls, path))


def parse_channels_cfg(args):
    """Parse channels.cfg from pmaports.git, origin/master branch.

    Reference: https://postmarketos.org/channels.cfg

    :returns: dict like: {"meta": {"recommended": "edge"},
        "channels": {"edge": {"description": ...,
        "branch_pmaports": ...,
        "branch_aports": ...,
        "mirrordir_alpine": ...},
        ...}}
    """
    # Cache during one pmbootstrap run
    cache_key = "pmb.helpers.git.parse_channels_cfg"
    if pmb.helpers.other.cache[cache_key]:
        return pmb.helpers.other.cache[cache_key]

    # Read with configparser
    cfg = configparser.ConfigParser()
    if args.config_channels:
        cfg.read([args.config_channels])
    else:
        remote = get_upstream_remote(args, "pmaports")
        command = ["git", "show", f"{remote}/master:channels.cfg"]
        stdout = pmb.helpers.run.user_output(command, args.aports,
                                      check=False)
        try:
            cfg.read_string(stdout)
        except configparser.MissingSectionHeaderError:
            logging.info("NOTE: fix this by fetching your pmaports.git, e.g."
                         " with 'pmbootstrap pull'")
            raise RuntimeError("Failed to read channels.cfg from"
                               f" '{remote}/master' branch of your local"
                               " pmaports clone")

    # Meta section
    ret: Dict[str, Dict[str, str | Dict[str, str]]] = {"channels": {}}
    ret["meta"] = {"recommended": cfg.get("channels.cfg", "recommended")}

    # Channels
    for channel in cfg.sections():
        if channel == "channels.cfg":
            continue  # meta section

        channel_new = pmb.helpers.pmaports.get_channel_new(channel)

        ret["channels"][channel_new] = {}
        for key in ["description", "branch_pmaports", "branch_aports",
                    "mirrordir_alpine"]:
            value = cfg.get(channel, key)
            # FIXME: how to type this properly??
            ret["channels"][channel_new][key] = value # type: ignore[index]

    pmb.helpers.other.cache[cache_key] = ret
    return ret


def get_branches_official(args: PmbArgs, name_repo):
    """Get all branches that point to official release channels.

    :returns: list of supported branches, e.g. ["master", "3.11"]
    """
    # This functions gets called with pmaports and aports_upstream, because
    # both are displayed in "pmbootstrap status". But it only makes sense
    # to display pmaports there, related code will be refactored soon (#1903).
    if name_repo != "pmaports":
        return ["master"]

    channels_cfg = parse_channels_cfg(args)
    ret = []
    for channel, channel_data in channels_cfg["channels"].items():
        ret.append(channel_data["branch_pmaports"])
    return ret


def pull(args: PmbArgs, name_repo):
    """Check if on official branch and essentially try ``git pull --ff-only``.

    Instead of really doing ``git pull --ff-only``, do it in multiple steps
    (``fetch, merge --ff-only``), so we can display useful messages depending
    on which part fails.

    :returns: integer, >= 0 on success, < 0 on error
    """
    branches_official = get_branches_official(args, name_repo)

    # Skip if repo wasn't cloned
    path = get_path(args, name_repo)
    if not os.path.exists(path):
        logging.debug(name_repo + ": repo was not cloned, skipping pull!")
        return 1

    # Skip if not on official branch
    branch = rev_parse(args, path, extra_args=["--abbrev-ref"])
    msg_start = "{} (branch: {}):".format(name_repo, branch)
    if branch not in branches_official:
        logging.warning("{} not on one of the official branches ({}), skipping"
                        " pull!"
                        "".format(msg_start, ", ".join(branches_official)))
        return -1

    # Skip if workdir is not clean
    if not clean_worktree(args, path):
        logging.warning(msg_start + " workdir is not clean, skipping pull!")
        return -2

    # Skip if branch is tracking different remote
    branch_upstream = get_upstream_remote(args, name_repo) + "/" + branch
    remote_ref = rev_parse(args, path, branch + "@{u}", ["--abbrev-ref"])
    if remote_ref != branch_upstream:
        logging.warning("{} is tracking unexpected remote branch '{}' instead"
                        " of '{}'".format(msg_start, remote_ref,
                                          branch_upstream))
        return -3

    # Fetch (exception on failure, meaning connection to server broke)
    logging.info(msg_start + " git pull --ff-only")
    if not args.offline:
        pmb.helpers.run.user(["git", "fetch"], path)

    # Skip if already up to date
    if rev_parse(args, path, branch) == rev_parse(args, path, branch_upstream):
        logging.info(msg_start + " already up to date")
        return 2

    # Skip if we can't fast-forward
    if not can_fast_forward(args, path, branch_upstream):
        logging.warning("{} can't fast-forward to {}, looks like you changed"
                        " the git history of your local branch. Skipping pull!"
                        "".format(msg_start, branch_upstream))
        return -4

    # Fast-forward now (should not fail due to checks above, so it's fine to
    # throw an exception on error)
    command = ["git", "merge", "--ff-only", branch_upstream]
    pmb.helpers.run.user(command, path, "stdout")
    return 0


def get_topdir(args: PmbArgs, path: Path):
    """Get top-dir of git repo.

    :returns: a string with the top dir of the git repository,
        or an empty string if it's not a git repository.
    """
    return pmb.helpers.run.user(["git", "rev-parse", "--show-toplevel"],
                                path, output_return=True, check=False).rstrip()


def get_files(args: PmbArgs, path):
    """Get all files inside a git repository, that are either already in the git tree or are not in gitignore.

    Do not list deleted files. To be used for creating a tarball of the git repository.

    :param path: top dir of the git repository

    :returns: all files in a git repository as list, relative to path
    """
    ret = []
    files = pmb.helpers.run.user_output(["git", "ls-files"], path).split("\n")
    files += pmb.helpers.run.user_output(["git", "ls-files",
                                                "--exclude-standard", "--other"],
                                         path).split("\n")
    for file in files:
        if os.path.exists(f"{path}/{file}"):
            ret += [file]

    return ret
