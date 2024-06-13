# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
from pathlib import Path
import sys
from typing import TextIO
import pmb.config

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
    
    def __init__(self, details_to_stdout: bool=False, quiet: bool=False):
        super().__init__()
        self.details_to_stdout = False
        self.quiet = False

    def emit(self, record):
        try:
            msg = self.format(record)

            # INFO or higher: Write to stdout
            if (not self.details_to_stdout and
                not self.quiet and
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
                    .replace(
                        "@BLUE@",
                        f"{styles['BLUE']}",
                    )
                    .replace(
                        "@YELLOW@",
                        f"{styles['YELLOW']}",
                    )
                    .replace(
                        "@RED@",
                        f"{styles['RED']}",
                    )
                    .replace(
                        "@GREEN@",
                        f"{styles['GREEN']}",
                    )
                    .replace(
                        "@END@",
                        f"{styles['END']}",
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


def init(logfile: Path, verbose: bool, details_to_stdout: bool=False):
    """Set log format and add the log file descriptor to logfd, add the verbose log level."""
    global logfd

    if "logfs" in globals():
        warning("Logging already initialized, skipping...")
        return

    # Set log file descriptor (logfd)
    if details_to_stdout:
        logfd = sys.stdout
    else:
        # Require containing directory to exist (so we don't create the work
        # folder and break the folder migration logic, which needs to set the
        # version upon creation)
        dir = os.path.dirname(logfile)
        if os.path.exists(dir):
            logfd = open(logfile, "a+")
            logfd.write("\n\n")
        else:
            logfd = open(os.devnull, "a+")

    # Set log format
    root_logger = logging.getLogger()
    root_logger.handlers = []
    formatter = logging.Formatter("[%(asctime)s] %(message)s",
                                  datefmt="%H:%M:%S")

    # Set log level
    add_verbose_log_level()
    root_logger.setLevel(logging.DEBUG)
    if verbose:
        root_logger.setLevel(VERBOSE)

    # Add a custom log handler
    handler = log_handler(details_to_stdout=details_to_stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logging.debug(f"Pmbootstrap v{pmb.__version__} (Python {sys.version})")
    if "--password" in sys.argv:
        sys.argv[sys.argv.index("--password")+1] = "[REDACTED]"
    logging.debug(f"$ pmbootstrap {' '.join(sys.argv)}")


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
