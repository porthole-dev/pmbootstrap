# Copyright 2025 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import pmb.helpers.repo
import pmb.parse.apkindex

from pmb.aportgen.gcc import depends_for_sonames
from pmb.core.apkindex_block import ApkindexBlock


def test_depends_for_sonames(monkeypatch):
    fake_apkindex: dict[str, dict[str, ApkindexBlock]] = {}
    arch_libc = "x86_64"
    libraries = {
        "so:libisl.so.*": "isl*",
        "so:libmpc.so.*": "mpc1",
    }

    def fake_apkindex_files(*args, **kwargs):
        return "fake/path/to/APKINDEX.tar.gz"

    def fake_apkindex_parse(*args, **kwargs):
        print(fake_apkindex)
        return fake_apkindex

    monkeypatch.setattr(pmb.helpers.repo, "apkindex_files", fake_apkindex_files)
    monkeypatch.setattr(pmb.parse.apkindex, "parse", fake_apkindex_parse)

    # Empty apkindex -> can't find it
    with pytest.raises(RuntimeError) as e:
        depends_for_sonames(libraries, arch_libc)
    assert "not provided by any package" in str(e.value)

    # APKINDEX filled, the highest libisl.so must be picked
    fake_apkindex = {
        "so:libisl.so.23": {
            "isl25": {},
            "isl26": {},
        },
        "so:libisl.so.22": {
            "isl24": {},
        },
        "so:libmpc.so.3": {
            "mpc1": {},
        },
    }

    assert depends_for_sonames(libraries, arch_libc) == [
        "so:libisl.so.23",
        "so:libmpc.so.3",
    ]
