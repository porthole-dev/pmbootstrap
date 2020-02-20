# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
import sys

import pmb_test  # noqa
import pmb.helpers.repo


@pytest.fixture
def args(tmpdir, request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_hash():
    url = "https://nl.alpinelinux.org/alpine/edge/testing"
    hash = "865a153c"
    assert pmb.helpers.repo.hash(url, 8) == hash


def test_alpine_apkindex_path(args):
    func = pmb.helpers.repo.alpine_apkindex_path
    args.mirror_alpine = "http://dl-cdn.alpinelinux.org/alpine/"
    ret = args.work + "/cache_apk_armhf/APKINDEX.30e6f5af.tar.gz"
    assert func(args, "testing", "armhf") == ret
