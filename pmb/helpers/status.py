# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import pmb.config.workdir


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
    ret = print_checks(args, details)

    return ret
