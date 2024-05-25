# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path, PurePath
import shutil
from typing import Sequence

import pmb.config
import pmb.chroot
import pmb.chroot.binfmt
import pmb.helpers.run
import pmb.helpers.run_core
from pmb.core import Chroot
from pmb.types import Env, PathString, PmbArgs


def executables_absolute_path():
    """
    Get the absolute paths to the sh and chroot executables.
    """
    ret = {}
    for binary in ["sh", "chroot"]:
        path = shutil.which(binary, path=pmb.config.chroot_host_path)
        if not path:
            raise RuntimeError(f"Could not find the '{binary}'"
                               " executable. Make sure that it is in"
                               " your current user's PATH.")
        ret[binary] = path
    return ret


def root(cmd: Sequence[PathString], chroot: Chroot=Chroot.native(), working_dir: PurePath=PurePath("/"), output="log",
         output_return=False, check=None, env={},
         disable_timeout=False, add_proxy_env_vars=True):
    """
    Run a command inside a chroot as root.

    :param env: dict of environment variables to be passed to the command, e.g.
                {"JOBS": "5"}
    :param working_dir: chroot-relative working directory
    :param add_proxy_env_vars: if True, preserve HTTP_PROXY etc. vars from host
                               environment. pmb.chroot.user sets this to False
                               when calling pmb.chroot.root, because it already
                               makes the variables part of the cmd argument.

    See pmb.helpers.run_core.core() for a detailed description of all other
    arguments and the return value.
    """

    # Convert any Path objects to their string representation
    cmd_str = [os.fspath(x) for x in cmd]

    # Readable log message (without all the escaping)
    msg = f"({chroot}) % "
    for key, value in env.items():
        msg += f"{key}={value} "
    if working_dir != PurePath("/"):
        msg += f"cd {working_dir}; "
    msg += " ".join(cmd_str)

    # Merge env with defaults into env_all
    env_all: Env = {"CHARSET": "UTF-8",
               "HISTFILE": "~/.ash_history",
               "HOME": "/root",
               "LANG": "UTF-8",
               "PATH": pmb.config.chroot_path,
               "PYTHONUNBUFFERED": "1",
               "SHELL": "/bin/ash",
               "TERM": "xterm"}
    for key, value in env.items():
        env_all[key] = value
    if add_proxy_env_vars:
        pmb.helpers.run_core.add_proxy_env_vars(env_all)

    # Build the command in steps and run it, e.g.:
    # cmd: ["echo", "test"]
    # cmd_chroot: ["/sbin/chroot", "/..._native", "/bin/sh", "-c", "echo test"]
    # cmd_sudo: ["sudo", "env", "-i", "sh", "-c", "PATH=... /sbin/chroot ..."]
    executables = executables_absolute_path()
    cmd_chroot = [executables["chroot"], chroot.path, "/bin/sh", "-c",
                  pmb.helpers.run_core.flat_cmd(cmd_str, Path(working_dir))]
    cmd_sudo = pmb.config.sudo([
        "env", "-i", executables["sh"], "-c",
        pmb.helpers.run_core.flat_cmd(cmd_chroot, env=env_all)]
    )
    return pmb.helpers.run_core.core(msg, cmd_sudo, None, output,
                                     output_return, check, True,
                                     disable_timeout)


def user(cmd, chroot: Chroot=Chroot.native(), working_dir: Path = Path("/"), output="log",
         output_return=False, check=None, env={}):
    """
    Run a command inside a chroot as "user". We always use the BusyBox
    implementation of 'su', because other implementations may override the PATH
    environment variable (#1071).

    :param env: dict of environment variables to be passed to the command, e.g.
                {"JOBS": "5"}

    See pmb.helpers.run_core.core() for a detailed description of all other
    arguments and the return value.
    """
    env = env.copy()
    pmb.helpers.run_core.add_proxy_env_vars(env)

    if "HOME" not in env:
        env["HOME"] = "/home/pmos"

    flat_cmd = pmb.helpers.run_core.flat_cmd(cmd, env=env)
    cmd = ["busybox", "su", "pmos", "-c", flat_cmd]
    return pmb.chroot.root(cmd, chroot, working_dir, output,
                           output_return, check, {},
                           add_proxy_env_vars=False)


def exists(username, chroot: Chroot=Chroot.native()):
    """
    Checks if username exists in the system

    :param username: User name
    :returns: bool
    """
    output = pmb.chroot.root(["getent", "passwd", username],
                             chroot, output_return=True, check=False)
    return len(output) > 0

