# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from typing import Final

import pytest

import pmb.helpers.logging
import pmb.helpers.pmaports
from pmb.core.arch import Arch
from pmb.parse._apkbuild import _apkbuild_from_lines, read_file
from pmb.parse._apkbuild_cond import resolve

TESTDIR: Final[Path] = Path(__file__).parent.parent / "data/tests"


@pytest.fixture(autouse=True)
def verbose_log_level() -> None:
    pmb.helpers.logging.add_verbose_log_level()


def run(code: str, carch: str = "aarch64") -> list[str]:
    lines = [line + "\n" for line in code.strip("\n").split("\n")]
    return [line.rstrip("\n") for line in resolve(lines, {"CARCH": carch})]


def parse(arch: Arch | None) -> dict:
    path = TESTDIR / "APKBUILD.arch-conditionals"
    return _apkbuild_from_lines(read_file(path), path, check_pkgname=False, arch=arch)


def test_case_takes_the_matching_branch() -> None:
    code = """
case "$CARCH" in
x86*) a=x86 ;;
armv7|aarch64)
	a="arm"
	b=$a
	;;
*) a=other ;;
esac
"""
    assert run(code, "x86_64") == ["a=x86"]
    assert run(code, "aarch64") == ['a="arm"', "b=$a"]
    assert run(code, "riscv64") == ["a=other"]


def test_case_without_match_emits_nothing() -> None:
    assert run("pre=1\ncase $CARCH in\nx86) a=1;;\nesac\npost=1") == ["pre=1", "post=1"]


def test_quoted_pattern_is_literal() -> None:
    assert run('case "$CARCH" in\n"aarch*") a=1;;\nesac') == []


def test_if_elif_else() -> None:
    code = """
_v=3
if [ "$CARCH" = x86 ]; then
	a=1
elif test "$_v" -gt 2 && [ -n "$CARCH" ]
then
	a=2
else
	a=3
fi
"""
    assert run(code, "x86") == ["_v=3", "a=1"]
    assert run(code, "armv7") == ["_v=3", "a=2"]


def test_and_or_list() -> None:
    code = '[ "$CARCH" != aarch64 ] && a="yes" || a="no"'
    assert run(code, "aarch64") == ['a="no"']
    assert run(code, "x86_64") == ['a="yes"']


def test_multiline_value_in_branch() -> None:
    code = """
case "$CARCH" in
aarch64)
	makedepends="
		$makedepends
		rust
		"
	;;
esac
"""
    assert run(code) == ['makedepends="', "$makedepends", "rust", '"']


def test_nested_blocks() -> None:
    code = """
if [ "$CARCH" = aarch64 ]; then
	case "$CARCH" in
	aarch*) a=1 ;;
	esac
fi
"""
    assert run(code) == ["a=1"]


def test_unknown_variable_leaves_block_alone() -> None:
    code = '[ -z "$BOOTSTRAP" ] && a=1\nif [ "$CBUILD" != "$CHOST" ]; then\n\tb=1\nfi'
    assert run(code) == code.split("\n")


def test_variable_assigned_in_unevaluated_block_becomes_unknown() -> None:
    code = """
_x=1
for i in 1 2; do _x=2; done
[ "$_x" = 1 ] && a=1
"""
    assert run(code)[-1] == '[ "$_x" = 1 ] && a=1'


def test_command_substitution_leaves_block_alone() -> None:
    code = 'if [ "$(uname -m)" = aarch64 ]; then\n\ta=1\nfi'
    assert run(code) == code.split("\n")


def test_functions_are_not_evaluated() -> None:
    code = """
build() {
	case "$CARCH" in
	aarch64) a=1 ;;
	esac
}
check() (
	[ "$CARCH" = aarch64 ] && a=2
)
"""
    assert run(code) == code.strip("\n").split("\n")


def test_unparsable_file_is_unchanged() -> None:
    code = 'a="unterminated\ncase "$CARCH" in\naarch64) b=1 ;;\nesac'
    assert run(code) == code.split("\n")


def test_apkbuild_with_arch() -> None:
    aarch64 = parse(Arch.aarch64)
    assert aarch64["makedepends"] == ["meson", "clang23-dev", "rust"]
    assert list(aarch64["subpackages"]) == ["hello-arch-doc", "hello-arch-vulkan"]
    assert aarch64["subpackages"]["hello-arch-vulkan"]["depends"] == ["vulkan-aarch64"]
    assert aarch64["depends"] == ["not-x86_64"]
    assert aarch64["checkdepends"] == ["not-armv7"]
    assert aarch64["options"] == ["!check"]

    armv7 = parse(Arch.armv7)
    assert armv7["options"] == ["!check", "textrels"]
    assert armv7["checkdepends"] == []
    assert armv7["subpackages"]["hello-arch-vulkan"]["depends"] == ["vulkan-other"]

    x86_64 = parse(Arch.x86_64)
    assert x86_64["makedepends"] == ["meson", "clang23-dev", "rust"]
    assert list(x86_64["subpackages"]) == ["hello-arch-doc"]
    assert x86_64["depends"] == ["x86_64-only"]

    riscv64 = parse(Arch.riscv64)
    assert riscv64["makedepends"] == ["meson"]
    assert riscv64["depends"] == ["riscv-only"]


def test_apkbuild_without_arch_skips_conditionals() -> None:
    apkbuild = parse(None)
    assert apkbuild["makedepends"] == ["meson"]
    assert list(apkbuild["subpackages"]) == ["hello-arch-doc"]
    assert apkbuild["depends"] == []


def test_pmaports_get_evaluates_for_arch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    aport = tmp_path / "hello-arch"
    aport.mkdir()
    (aport / "APKBUILD").write_text((TESTDIR / "APKBUILD.arch-conditionals").read_text())
    monkeypatch.setattr(pmb.helpers.pmaports, "find", lambda *_args, **_kwargs: aport)

    assert "rust" in pmb.helpers.pmaports.get("hello-arch", arch=Arch.aarch64)["makedepends"]
    assert "rust" not in pmb.helpers.pmaports.get("hello-arch", arch=Arch.riscv64)["makedepends"]
    assert "rust" not in pmb.helpers.pmaports.get("hello-arch")["makedepends"]
