# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path
import pmb.helpers.run_core
from typing import Any, Dict, List, Optional, Sequence
from pmb.core.types import PathString, PmbArgs


def user(args: PmbArgs, cmd: Sequence[PathString], working_dir: Path=Path("/"), output: str="log", output_return: bool=False,
         check: Optional[bool]=None, env: Dict[Any, Any]={}, sudo: bool=False) -> str:
    """
    Run a command on the host system as user.

    :param env: dict of environment variables to be passed to the command, e.g.
                {"JOBS": "5"}

    See pmb.helpers.run_core.core() for a detailed description of all other
    arguments and the return value.
    """
    cmd_parts = [os.fspath(x) for x in cmd]
    # Readable log message (without all the escaping)
    msg = "% "
    for key, value in env.items():
        msg += key + "=" + value + " "
    if working_dir != Path("/"):
        msg += f"cd {os.fspath(working_dir)}; "
    msg += " ".join(cmd_parts)

    # Add environment variables and run
    env = env.copy()
    pmb.helpers.run_core.add_proxy_env_vars(env)
    if env:
        cmd_parts = ["sh", "-c", pmb.helpers.run_core.flat_cmd(cmd_parts, env=env)]
    return pmb.helpers.run_core.core(args, msg, cmd_parts, working_dir, output,
                                     output_return, check, sudo)


def root(args: PmbArgs, cmd: Sequence[PathString], working_dir=None, output="log", output_return=False,
         check=None, env={}):
    """Run a command on the host system as root, with sudo or doas.

    :param env: dict of environment variables to be passed to the command, e.g.
                {"JOBS": "5"}

    See pmb.helpers.run_core.core() for a detailed description of all other
    arguments and the return value.
    """
    env = env.copy()
    pmb.helpers.run_core.add_proxy_env_vars(env)

    if env:
        cmd = ["sh", "-c", pmb.helpers.run_core.flat_cmd(cmd, env=env)]
    cmd = pmb.config.sudo(cmd)

    return user(args, cmd, working_dir, output, output_return, check, env,
                True)
