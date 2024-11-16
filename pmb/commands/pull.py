# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from pmb import commands
import pmb.helpers.git
import pmb.config
import logging


class Pull(commands.Command):
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        failed = []
        for repo in pmb.config.git_repos.keys():
            if pmb.helpers.git.pull(repo) < 0:
                failed.append(repo)

        if not failed:
            return

        logging.info("---")
        logging.info("WARNING: failed to update: " + ", ".join(failed))
        logging.info("")
        logging.info("'pmbootstrap pull' will only update the repositories, if:")
        logging.info("* they are on an officially supported branch (e.g. master)")
        logging.info("* the history is not conflicting (fast-forward is possible)")
        logging.info("* the git workdirs are clean")
        logging.info("You have changed mentioned repositories, so they don't meet")
        logging.info("these conditions anymore.")
        logging.info("")
        logging.info("Fix and try again:")
        for name_repo in failed:
            logging.info(f"* {pmb.helpers.git.get_path(name_repo)}")
        logging.info("---")
