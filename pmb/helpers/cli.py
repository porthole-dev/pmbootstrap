# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import logging
import re


def ask(args, question="Continue?", choices=["y", "n"], default="n",
        lowercase_answer=True, validation_regex=None):
    """
    Ask a question on the terminal. When validation_regex is set, the user gets
    asked until the answer matches the regex.
    :returns: the user's answer
    """
    while True:
        date = datetime.datetime.now().strftime("%H:%M:%S")
        question_full = "[" + date + "] " + question
        if choices:
            question_full += " (" + str.join("/", choices) + ")"
        if default:
            question_full += " [" + str(default) + "]"

        ret = input(question_full + ": ")
        if lowercase_answer:
            ret = ret.lower()
        if ret == "":
            ret = str(default)

        args.logfd.write(question_full + " " + ret + "\n")
        args.logfd.flush()

        # Validate with regex
        if not validation_regex:
            return ret

        pattern = re.compile(validation_regex)
        if pattern.match(ret):
            return ret

        logging.fatal("ERROR: Input did not pass validation (regex: " +
                      validation_regex + "). Please try again.")


def confirm(args, question="Continue?", default=False):
    """
    Convenience wrapper around ask for simple yes-no questions with validation.
    :returns: True for "y", False for "n"
    """
    default_str = "y" if default else "n"
    if (args.assume_yes):
        logging.info(question + " (y/n) [" + default_str + "]: y")
        return True
    answer = ask(args, question, ["y", "n"], default_str, True, "(y|n)")
    return answer == "y"
