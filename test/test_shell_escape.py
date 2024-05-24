# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from typing import Any
from pmb.core.types import Env, PmbArgs
import pytest

import pmb_test  # noqa
import pmb.chroot.run
import pmb.helpers.run
import pmb.helpers.run_core
import pmb.helpers.logging


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    args.log = pmb.config.work / "log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(pmb.helpers.logging.logfd.close)
    return args


def test_shell_escape(args: PmbArgs):
    cmds = {"test\n": ["echo", "test"],
            "test && test\n": ["echo", "test", "&&", "test"],
            "test ; test\n": ["echo", "test", ";", "test"],
            "'test\"test\\'\n": ["echo", "'test\"test\\'"],
            "*\n": ["echo", "*"],
            "$PWD\n": ["echo", "$PWD"],
            "hello world\n": ["printf", "%s world\n", "hello"]}
    for expected, cmd in cmds.items():
        copy = list(cmd)
        core = pmb.helpers.run_core.core(args, str(cmd), cmd,
                                         output_return=True)
        assert expected == core
        assert cmd == copy

        user = pmb.helpers.run.user(args, cmd, output_return=True)
        assert expected == user
        assert cmd == copy

        root = pmb.helpers.run.root(args, cmd, output_return=True)
        assert expected == root
        assert cmd == copy

        chroot_root = pmb.chroot.run(args, cmd, output_return=True)
        assert expected == chroot_root
        assert cmd == copy

        chroot_user = pmb.chroot.user(args, cmd, output_return=True)
        assert expected == chroot_user
        assert cmd == copy


def test_shell_escape_env(args: PmbArgs):
    key = "PMBOOTSTRAP_TEST_ENVIRONMENT_VARIABLE"
    value = "long value with spaces and special characters: '\"\\!$test"
    env: Env = {key: value}
    cmd = ["sh", "-c", "env | grep " + key + " | grep -v SUDO_COMMAND"]
    ret = key + "=" + value + "\n"

    copy = list(cmd)
    func: Any = pmb.helpers.run.user
    assert func(args, cmd, output_return=True, env=env) == ret
    assert cmd == copy

    func = pmb.helpers.run.root
    assert func(args, cmd, output_return=True, env=env) == ret
    assert cmd == copy

    func = pmb.chroot.run
    assert func(args, cmd, output_return=True, env=env) == ret
    assert cmd == copy

    func = pmb.chroot.user
    assert func(args, cmd, output_return=True, env=env) == ret
    assert cmd == copy


def test_flat_cmd_simple():
    func = pmb.helpers.run_core.flat_cmd
    cmd = ["echo", "test"]
    ret = "echo test"
    env: Env = {}
    assert func(cmd, env=env) == ret


def test_flat_cmd_wrap_shell_string_with_spaces():
    func = pmb.helpers.run_core.flat_cmd
    cmd = ["echo", "string with spaces"]
    ret = "echo 'string with spaces'"
    env: Env = {}
    assert func(cmd, env=env) == ret


def test_flat_cmd_wrap_env_simple():
    func = pmb.helpers.run_core.flat_cmd
    cmd = ["echo", "test"]
    ret = "JOBS=5 echo test"
    env: Env = {"JOBS": "5"}
    assert func(cmd, env=env) == ret


def test_flat_cmd_wrap_env_spaces():
    func = pmb.helpers.run_core.flat_cmd
    cmd = ["echo", "test"]
    ret = "JOBS=5 TEST='spaces string' echo test"
    env: Env = {"JOBS": "5", "TEST": "spaces string"}
    assert func(cmd, env=env) == ret
