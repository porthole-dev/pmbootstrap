# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import pmb.chroot
import pmb.helpers.run
import pmb.helpers.run_core
from pmb.core import Chroot
from pmb.core.types import PathString, PmbArgs


def user(args: PmbArgs, cmd, chroot: Chroot=Chroot.native(), working_dir: Path = Path("/"), output="log",
         output_return=False, check=None, env={}, auto_init=True):
    """
    Run a command inside a chroot as "user". We always use the BusyBox
    implementation of 'su', because other implementations may override the PATH
    environment variable (#1071).

    :param env: dict of environment variables to be passed to the command, e.g.
                {"JOBS": "5"}
    :param auto_init: automatically initialize the chroot

    See pmb.helpers.run_core.core() for a detailed description of all other
    arguments and the return value.
    """
    env = env.copy()
    pmb.helpers.run_core.add_proxy_env_vars(env)

    if "HOME" not in env:
        env["HOME"] = "/home/pmos"

    flat_cmd = pmb.helpers.run_core.flat_cmd(cmd, env=env)
    cmd = ["busybox", "su", "pmos", "-c", flat_cmd]
    return pmb.chroot.root(args, cmd, chroot, working_dir, output,
                           output_return, check, {}, auto_init,
                           add_proxy_env_vars=False)


def exists(args: PmbArgs, username, chroot: Chroot=Chroot.native()):
    """
    Checks if username exists in the system

    :param username: User name
    :returns: bool
    """
    output = pmb.chroot.root(args, ["getent", "passwd", username],
                             chroot, output_return=True, check=False)
    return len(output) > 0
