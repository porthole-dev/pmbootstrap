# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import logging

import pmb.config
import pmb.config.workdir
import pmb.helpers.git


def print_config(args):
    """ Print an overview of what was set in "pmbootstrap init". """
    logging.info("*** CONFIG ***")
    info = args.deviceinfo
    logging.info("Device: {} ({}, \"{}\")"
                 .format(args.device, info["arch"], info["name"]))

    if pmb.parse._apkbuild.kernels(args, args.device):
        logging.info("Kernel: " + args.kernel)

    if args.extra_packages != "none":
        logging.info("Extra packages: {}".format(args.extra_packages))

    logging.info("User Interface: {}".format(args.ui))


def print_git_repos(args):
    logging.info("*** GIT REPOS ***")
    logging.info("Path: {}/cache_git".format(args.work))
    for repo in pmb.config.git_repos.keys():
        path = pmb.helpers.git.get_path(args, repo)
        if not os.path.exists(path):
            continue

        # Get branch name (if on branch) or current commit
        ref = pmb.helpers.git.rev_parse(args, path,
                                        extra_args=["--abbrev-ref"])
        if ref == "HEAD":
            ref = pmb.helpers.git.rev_parse(args, path)[0:8]

        logging.info("- {} ({})".format(repo, ref))


def print_checks_chroots_outdated(args, details):
    """ Check if chroots were zapped recently.
        :param details: if True, print each passing check instead of a summary
        :returns: list of unresolved checklist items """
    if pmb.config.workdir.chroots_outdated(args):
        logging.info("[NOK] Chroots not zapped recently")
        return ["Run 'pmbootststrap zap' to delete possibly outdated chroots"]
    elif details:
        logging.info("[OK ] Chroots zapped recently (or non-existing)")
    return []


def print_checks(args, details):
    """ :param details: if True, print each passing check instead of a summary
        :returns: True if all checks passed, False otherwise """
    logging.info("*** CHECKS ***")
    checklist = []
    checklist += print_checks_chroots_outdated(args, details)

    # All OK
    if not checklist:
        if not details:
            logging.info("All checks passed! \\o/")
        logging.info("")
        return True

    # Some NOK: print checklist
    logging.info("")
    logging.info("*** CHECKLIST ***")
    for item in checklist:
        logging.info("- " + item)
    logging.info("- Run 'pmbootstrap status' to verify that all is resolved")
    return False


def print_status(args, details=False):
    """ :param details: if True, print each passing check instead of a summary
        :returns: True if all checks passed, False otherwise """
    print_config(args)
    logging.info("")
    print_git_repos(args)
    logging.info("")
    ret = print_checks(args, details)

    return ret
