# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import socket
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

import pmb.chroot
import pmb.config
import pmb.helpers.run
from pmb.build.backend import abuild_env
from pmb.chroot.shutdown import kill_sccache
from pmb.core.arch import Arch
from pmb.core.chroot import Chroot
from pmb.core.config import Config
from pmb.core.context import Context, get_context
from pmb.types import CrossCompile


@pytest.mark.parametrize(
    "cross",
    [CrossCompile.UNNECESSARY, CrossCompile.CROSS_NATIVE2, CrossCompile.CROSSDIRECT],
)
def test_every_build_gets_a_chroot_local_sccache_socket(cross: CrossCompile) -> None:
    env = abuild_env(Context(Config()), Arch.aarch64, cross, 0)
    assert env["SCCACHE_SERVER_UDS"] == "/tmp/sccache.sock"
    # crossdirect runs sccache from its rustc wrapper, which inherits the variable
    assert ("RUSTC_WRAPPER" in env) == (cross != CrossCompile.CROSSDIRECT)


def _listen(path: Path) -> socket.socket:
    path.parent.mkdir(parents=True)
    cwd = os.getcwd()
    os.chdir(path.parent)  # AF_UNIX paths are limited to 108 bytes
    try:
        sock = socket.socket(socket.AF_UNIX)
        sock.bind(path.name)
    finally:
        os.chdir(cwd)
    return sock


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def test_kill_sccache_stops_each_chroots_server(
    pmb_args: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    work = get_context().config.work
    native = _listen(work / "chroot_native/tmp/sccache.sock")
    _touch(work / "chroot_native/usr/bin/sccache")
    foreign = _listen(work / "chroot_buildroot_aarch64/tmp/sccache.sock")
    _touch(work / "chroot_buildroot_aarch64/native/usr/bin/sccache")
    (work / "chroot_buildroot_armv7/tmp").mkdir(parents=True)

    stopped: list[tuple[Sequence[str], Chroot, dict[str, str]]] = []
    removed: list[Path] = []

    def root(cmd: Sequence[str], chroot: Chroot, env: dict[str, str], **_kwargs: Any) -> None:
        stopped.append((cmd, chroot, env))

    monkeypatch.setattr(pmb.chroot, "root", root)
    monkeypatch.setattr(pmb.helpers.run, "root", lambda cmd, **_kwargs: removed.append(cmd[-1]))

    kill_sccache()
    native.close()
    foreign.close()

    socket_env = {"SCCACHE_SERVER_UDS": pmb.config.sccache_server_uds}
    assert sorted(stopped, key=str) == sorted(
        [
            (["/usr/bin/sccache", "--stop-server"], Chroot.native(), socket_env),
            (
                ["/native/usr/bin/sccache", "--stop-server"],
                Chroot.buildroot(Arch.aarch64),
                {**socket_env, "LD_LIBRARY_PATH": "/native/lib:/native/usr/lib"},
            ),
        ],
        key=str,
    )
    assert sorted(removed) == sorted(
        [
            work / "chroot_native/tmp/sccache.sock",
            work / "chroot_buildroot_aarch64/tmp/sccache.sock",
        ]
    )
