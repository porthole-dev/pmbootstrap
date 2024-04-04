# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import sys
from typing import TextIO
import pmb.config
from pmb.core.types import PmbArgs

logfd: TextIO

CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET
VERBOSE = 5

class log_handler(logging.StreamHandler):
    """Write to stdout and to the already opened log file."""
    _args: PmbArgs
    
    def __init__(self, args: PmbArgs):
        super().__init__()
        self._args = args

    def emit(self, record):
        try:
            msg = self.format(record)

            # INFO or higher: Write to stdout
            if (not self._args.details_to_stdout and
                not self._args.quiet and
                    record.levelno >= logging.INFO):
                stream = self.stream

                styles = pmb.config.styles

                msg_col = (
                    msg.replace(
                        "NOTE:",
                        f"{styles['BLUE']}NOTE:{styles['END']}",
                        1,
                    )
                    .replace(
                        "WARNING:",
                        f"{styles['YELLOW']}WARNING:{styles['END']}",
                        1,
                    )
                    .replace(
                        "ERROR:",
                        f"{styles['RED']}ERROR:{styles['END']}",
                        1,
                    )
                    .replace(
                        "DONE!",
                        f"{styles['GREEN']}DONE!{styles['END']}",
                        1,
                    )
                    .replace(
                        "*** ",
                        f"{styles['GREEN']}*** ",
                        1,
                    )
                )

                msg_col += styles["END"]

                stream.write(msg_col)
                stream.write(self.terminator)
                self.flush()

            # Everything: Write to logfd
            msg = "(" + str(os.getpid()).zfill(6) + ") " + msg
            logfd.write(msg + "\n")
            logfd.flush()

        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self.handleError(record)


def add_verbose_log_level():
    """Add a new log level "verbose", which is below "debug".

    Also monkeypatch logging, so it can be used with logging.verbose().

    This function is based on work by Voitek Zylinski and sleepycal:
    https://stackoverflow.com/a/20602183
    All stackoverflow user contributions are licensed as CC-BY-SA:
    https://creativecommons.org/licenses/by-sa/3.0/
    """
    setattr(logging, "VERBOSE", VERBOSE)
    logging.addLevelName(VERBOSE, "VERBOSE")
    setattr(logging.Logger, "verbose", lambda inst, msg, * \
        args, **kwargs: inst.log(VERBOSE, msg, *args, **kwargs))
    setattr(logging, "verbose", lambda msg, *args, **kwargs: logging.log(VERBOSE,
                                                               msg, *args,
                                                               **kwargs))


def init(args: PmbArgs):
    """Set log format and add the log file descriptor to logfd, add the verbose log level."""
    global logfd
    # Set log file descriptor (logfd)
    if args.details_to_stdout:
        logfd = sys.stdout
    else:
        # Require containing directory to exist (so we don't create the work
        # folder and break the folder migration logic, which needs to set the
        # version upon creation)
        dir = os.path.dirname(args.log)
        if os.path.exists(dir):
            logfd = open(args.log, "a+")
        else:
            logfd = open(os.devnull, "a+")
            if args.action != "init":
                print(f"WARNING: Can't create log file in '{dir}', path"
                      " does not exist!")

    # Set log format
    root_logger = logging.getLogger()
    root_logger.handlers = []
    formatter = logging.Formatter("[%(asctime)s] %(message)s",
                                  datefmt="%H:%M:%S")

    # Set log level
    add_verbose_log_level()
    root_logger.setLevel(logging.DEBUG)
    if args.verbose:
        root_logger.setLevel(VERBOSE)

    # Add a custom log handler
    handler = log_handler(args)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def disable():
    logger = logging.getLogger()
    logger.disabled = True


# We have our own logging wrappers so we can make mypy happy
# by not calling the (undefined) logging.verbose() function.

def critical(msg: object, *args, **kwargs):
    logging.critical(msg, *args, **kwargs)


def fatal(msg: object, *args, **kwargs):
    logging.fatal(msg, *args, **kwargs)


def error(msg: object, *args, **kwargs):
    logging.error(msg, *args, **kwargs)


def warning(msg: object, *args, **kwargs):
    logging.warning(msg, *args, **kwargs)


def info(msg: object, *args, **kwargs):
    logging.info(msg, *args, **kwargs)


def debug(msg: object, *args, **kwargs):
    logging.debug(msg, *args, **kwargs)


def verbose(msg: object, *args, **kwargs):
    logging.verbose(msg, *args, **kwargs) # type: ignore[attr-defined]


def log(level: int, msg: object, *args, **kwargs):
    logging.log(level, msg, *args, **kwargs)
