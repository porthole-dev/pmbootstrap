# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import logging
import re
import readline


class ReadlineTabCompleter:
    """ Stores intermediate state for completer function """
    def __init__(self, options):
        """
        :param options: list of possible completions
        """
        self.options = sorted(options)
        self.matches = []

    def completer_func(self, input_text, iteration):
        """
        :param input_text: text that shall be autocompleted
        :param iteration: how many times "tab" was hit
        """
        # First time: build match list
        if iteration == 0:
            if input_text:
                self.matches = [s for s in self.options if s and s.startswith(input_text)]
            else:
                self.matches = self.options[:]

        # Return the N'th item from the match list, if we have that many.
        if iteration < len(self.matches):
            return self.matches[iteration]
        return None


def ask(args, question="Continue?", choices=["y", "n"], default="n",
        lowercase_answer=True, validation_regex=None, complete=None):
    """
    Ask a question on the terminal.
    :param question: display prompt
    :param choices: short list of possible answers, displayed after prompt if set
    :param default: default value to return if user doesn't input anything
    :param lowercase_answer: if True, convert return value to lower case
    :param validation_regex: if set, keep asking until regex matches
    :param complete: set to a list to enable tab completion
    """
    while True:
        date = datetime.datetime.now().strftime("%H:%M:%S")
        question_full = "[" + date + "] " + question
        if choices:
            question_full += " (" + str.join("/", choices) + ")"
        if default:
            question_full += " [" + str(default) + "]"

        if complete:
            readline.parse_and_bind('tab: complete')
            delims = readline.get_completer_delims()
            if '-' in delims:
                delims = delims.replace('-', '')
                readline.set_completer_delims(delims)
            readline.set_completer(ReadlineTabCompleter(complete).completer_func)

        ret = input(question_full + ": ")

        # Stop completing (question is answered)
        if complete:
            readline.set_completer(None)

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


def confirm(args, question="Continue?", default=False, no_assumptions=False):
    """
    Convenience wrapper around ask for simple yes-no questions with validation.

    :param no_assumptions: ask for confirmation, even if "pmbootstrap -y' is set
    :returns: True for "y", False for "n"
    """
    default_str = "y" if default else "n"
    if args.assume_yes and not no_assumptions:
        logging.info(question + " (y/n) [" + default_str + "]: y")
        return True
    answer = ask(args, question, ["y", "n"], default_str, True, "(y|n)")
    return answer == "y"
