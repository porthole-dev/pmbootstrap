# Copyright 2023 Johannes Marbach, Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path
from typing import List, Sequence

import pmb.chroot.run
import pmb.config.pmaports
from pmb.core.types import PathString, PmbArgs
import pmb.helpers.cli
import pmb.helpers.run
import pmb.helpers.run_core
import pmb.parse.version


def _prepare_fifo(args: PmbArgs):
    """Prepare the progress fifo for reading / writing.

    :param chroot: whether to run the command inside the chroot or on the host
    :param suffix: chroot suffix. Only applies if the "chroot" parameter is
                   set to True.
    :returns: A tuple consisting of the path to the fifo as needed by apk to
              write into it (relative to the chroot, if applicable) and the
              path of the fifo as needed by cat to read from it (always
              relative to the host)
    """
    pmb.helpers.run.root(args, ["mkdir", "-p", pmb.config.work / "tmp"])
    fifo = fifo_outside = pmb.config.work / "tmp/apk_progress_fifo"
    if os.path.exists(fifo_outside):
        pmb.helpers.run.root(args, ["rm", "-f", fifo_outside])
    pmb.helpers.run.root(args, ["mkfifo", fifo_outside])
    return (fifo, fifo_outside)


def _create_command_with_progress(command, fifo):
    """Build a full apk command from a subcommand, set up to redirect progress into a fifo.

    :param command: apk subcommand in list form
    :param fifo: path of the fifo
    :returns: full command in list form
    """
    flags = ["--no-progress", "--progress-fd", "3"]
    command_full = [command[0]] + flags + command[1:]
    command_flat = pmb.helpers.run_core.flat_cmd(command_full)
    command_flat = f"exec 3>{fifo}; {command_flat}"
    return ["sh", "-c", command_flat]


def _compute_progress(line):
    """Compute the progress as a number between 0 and 1.

    :param line: line as read from the progress fifo
    :returns: progress as a number between 0 and 1
    """
    if not line:
        return 1
    cur_tot = line.rstrip().split('/')
    if len(cur_tot) != 2:
        return 0
    cur = float(cur_tot[0])
    tot = float(cur_tot[1])
    return cur / tot if tot > 0 else 0


def apk_with_progress(args: PmbArgs, command: Sequence[PathString]):
    """Run an apk subcommand while printing a progress bar to STDOUT.

    :param command: apk subcommand in list form
    :param chroot: whether to run commands inside the chroot or on the host
    :param suffix: chroot suffix. Only applies if the "chroot" parameter is
                   set to True.
    :raises RuntimeError: when the apk command fails
    """
    fifo, fifo_outside = _prepare_fifo(args)
    _command: List[str] = [os.fspath(c) for c in command]
    command_with_progress = _create_command_with_progress(_command, fifo)
    log_msg = " ".join(_command)
    with pmb.helpers.run.root(args, ['cat', fifo],
              output="pipe") as p_cat:
        with pmb.helpers.run.root(args, command_with_progress,
                  output="background") as p_apk:
            while p_apk.poll() is None:
                line = p_cat.stdout.readline().decode('utf-8')
                progress = _compute_progress(line)
                pmb.helpers.cli.progress_print(args, progress)
            pmb.helpers.cli.progress_flush(args)
            pmb.helpers.run_core.check_return_code(args, p_apk.returncode,
                                                   log_msg)


def check_outdated(args: PmbArgs, version_installed, action_msg):
    """Check if the provided alpine version is outdated.

    This depends on the alpine mirrordir (edge, v3.12, ...) related to currently checked out
    pmaports branch.

    :param version_installed: currently installed apk version, e.g. "2.12.1-r0"
    :param action_msg: string explaining what the user should do to resolve
                       this
    :raises: RuntimeError if the version is outdated
    """
    channel_cfg = pmb.config.pmaports.read_config_channel(args)
    mirrordir_alpine = channel_cfg["mirrordir_alpine"]
    version_min = pmb.config.apk_tools_min_version[mirrordir_alpine]

    if pmb.parse.version.compare(version_installed, version_min) >= 0:
        return

    raise RuntimeError("Found an outdated version of the 'apk' package"
                       f" manager ({version_installed}, expected at least:"
                       f" {version_min}). {action_msg}")
