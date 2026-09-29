# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression: a C dependency initializes the chroot before Rust needs sccache."""

import ast
from pathlib import Path
from types import SimpleNamespace


def test_cache_install_after_chroot_initialization() -> None:
    source = (Path(__file__).parents[2] / "pmb/build/_package.py").read_text()
    setup = source.split("        # One time chroot initialization\n", 1)[1]
    setup = setup.split("        if (strict or cross != prev_cross)", 1)[0]
    setup = "\n".join(line[8:] for line in setup.splitlines())
    calls: list[tuple[list[str], str]] = []
    pmb = SimpleNamespace(
        build=SimpleNamespace(init=lambda _: False),
        chroot=SimpleNamespace(
            apk=SimpleNamespace(install=lambda packages, chroot: calls.append((packages, chroot)))
        ),
    )
    # Execute only the checked-out source block, with chroot operations stubbed.
    exec(  # ruff:ignore[exec-builtin]
        compile(ast.parse(setup), "chroot-setup", "exec"),
        {
            "pmb": pmb,
            "hostchroot": "native",
            "buildchroot": "native",
            "all_dependencies": ["cargo"],
        },
    )
    assert calls == [(["sccache"], "native")]


if __name__ == "__main__":
    test_cache_install_after_chroot_initialization()
