# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.build.backend import rust_cross_native2_env
from pmb.core.arch import Arch


def test_rust_cross_native2_env_aarch64() -> None:
    env = rust_cross_native2_env(Arch.aarch64)
    assert env["CARGO_BUILD_TARGET"] == "aarch64-alpine-linux-musl"
    assert env["CARGO_TARGET_AARCH64_ALPINE_LINUX_MUSL_LINKER"] == "aarch64-alpine-linux-musl-gcc"
    assert env["RUSTFLAGS"] == "--sysroot=/mnt/sysroot/usr -Clink-arg=--sysroot=/mnt/sysroot"
    assert env["BINDGEN_EXTRA_CLANG_ARGS_aarch64_alpine_linux_musl"] == (
        "--target=aarch64-alpine-linux-musl --sysroot=/mnt/sysroot"
    )


def test_rust_cross_native2_env_sets_a_build_target() -> None:
    # RUSTFLAGS only stays off build scripts and proc-macros while a build
    # target is set, and the bindgen arguments stay target-scoped.
    env = rust_cross_native2_env(Arch.armv7)
    assert "CARGO_BUILD_TARGET" in env
    assert "BINDGEN_EXTRA_CLANG_ARGS" not in env
    assert env["CARGO_BUILD_TARGET"] == "armv7-alpine-linux-musleabihf"
