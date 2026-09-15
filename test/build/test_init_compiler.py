# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
import importlib
from collections.abc import Collection
from typing import Any

import pytest

import pmb.chroot.apk
from pmb.core.arch import Arch
from pmb.core.chroot import Chroot
from pmb.core.config import Config
from pmb.core.context import Context
from pmb.types import CrossCompile

# pmb.build.init is also the name of a function in pmb.build
build_init = importlib.import_module("pmb.build.init")


def test_crossdirect_rust_native_depends(monkeypatch: pytest.MonkeyPatch) -> None:
    installs: list[tuple[list[str], bool]] = []

    def install(packages: Collection[str], chroot: Chroot, build: bool = True) -> None:
        assert chroot == Chroot.native()
        installs.append((list(packages), build))

    def providers(package: str, *_args: Any, **_kwargs: Any) -> dict:
        # libcamera-dev is in a binary repo, only-in-pmaports-dev is not
        return {} if package == "only-in-pmaports-dev" else {package: None}

    monkeypatch.setattr(pmb.chroot, "init", lambda _chroot: None)
    monkeypatch.setattr(pmb.chroot.apk, "install", install)
    monkeypatch.setattr(build_init.apkindex, "providers", providers)
    context = Context(Config())
    context.ccache = False

    depends = ["cargo", "libcamera-dev", "only-in-pmaports-dev"]
    build_init.init_compiler(context, depends, CrossCompile.CROSSDIRECT, Arch.aarch64)
    assert installs[1:] == [
        (["cargo", "libcamera-dev"], False),
        (["only-in-pmaports-dev"], True),
    ]

    # cross-native2 installs build dependencies elsewhere
    installs.clear()
    build_init.init_compiler(context, depends, CrossCompile.CROSS_NATIVE2, Arch.aarch64)
    assert len(installs) == 1
    assert "libcamera-dev" not in installs[0][0]
