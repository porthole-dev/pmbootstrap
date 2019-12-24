"""
Copyright 2020 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import os

import pmb.build
import pmb.chroot.apk
import pmb.config
import pmb.helpers.run


def clone(args, name_repo, shallow=True):
    """ Clone a git repository to $WORK/cache_git/$name_repo.

        :param name_repo: short alias used for the repository name, from
                          pmb.config.git_repos (e.g. "aports_upstream",
                          "pmaports")
        :param shallow: only clone the last revision of the repository, instead
                        of the entire repository (faster, saves bandwith) """
    # Check for repo name in the config
    if name_repo not in pmb.config.git_repos:
        raise ValueError("No git repository configured for " + name_repo)

    # Skip if already checked out
    path = args.work + "/cache_git/" + name_repo
    if os.path.exists(path):
        return

    # Build git command
    url = pmb.config.git_repos[name_repo]
    command = ["git", "clone"]
    if shallow:
        command += ["--depth=1"]
    command += [url, path]

    # Create parent dir and clone
    logging.info("Clone git repository: " + url)
    os.makedirs(args.work + "/cache_git", exist_ok=True)
    pmb.helpers.run.user(args, command, output="stdout")


def rev_parse(args, revision="HEAD"):
    """ Run "git rev-parse" in the pmaports.git dir.

        :returns: commit string like "90cd0ad84d390897efdcf881c0315747a4f3a966"
    """

    rev = pmb.helpers.run.user(args, ["git", "rev-parse", revision],
                               args.aports, output_return=True)
    return rev.rstrip()
