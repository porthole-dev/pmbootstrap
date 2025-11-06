# Copyright 2025 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.build.envkernel import match_kbuild_out, find_kbuild_output_dir

import pytest


def test_match_kbuild_out() -> None:
    # Valid.
    assert match_kbuild_out('"$builddir"/include/config/kernel.release') == ""

    # Invalid.
    assert match_kbuild_out("mkdir") is None


def test_find_kbuild_output_dir() -> None:
    # Valid.
    assert find_kbuild_output_dir(["downstreamkernel_package"]) == ""
    assert find_kbuild_output_dir(["       downstreamkernel_package   "]) == ""
    assert find_kbuild_output_dir(['    downstreamkernel_package "$builddir"']) == ""
    assert find_kbuild_output_dir(["", "", "", "downstreamkernel_package", ""]) == ""

    # Invalid.
    with pytest.raises(RuntimeError):
        find_kbuild_output_dir([])
    with pytest.raises(RuntimeError):
        find_kbuild_output_dir(["", "", ""])
    with pytest.raises(RuntimeError):
        find_kbuild_output_dir(["", "hello!", ""])
