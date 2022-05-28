# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
import sys

import pmb_test  # noqa
import pmb.chroot.apk


@pytest.fixture
def args(tmpdir, request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(pmb.helpers.logging.logfd.close)
    return args


def test_install_build(monkeypatch, args):
    func = pmb.chroot.apk.install_build
    ret_apkindex_package = None

    def fake_build_package(args, package, arch):
        return "build-pkg"
    monkeypatch.setattr(pmb.build, "package", fake_build_package)

    def fake_apkindex_package(args, package, arch, must_exist):
        return ret_apkindex_package
    monkeypatch.setattr(pmb.parse.apkindex, "package", fake_apkindex_package)

    package = "hello-world"
    arch = "x86_64"

    # invoked as pmb install, build_pkgs_on_install disabled
    args.action = "install"
    args.build_pkgs_on_install = False
    with pytest.raises(RuntimeError) as e:
        func(args, package, arch)
    assert "no binary package found" in str(e.value)

    # invoked as pmb install, build_pkgs_on_install disabled, binary exists
    args.action = "install"
    args.build_pkgs_on_install = False
    ret_apkindex_package = {"pkgname": "hello-world"}
    assert func(args, package, arch) is None

    # invoked as pmb install, build_pkgs_on_install enabled
    args.action = "install"
    args.build_pkgs_on_install = True
    assert func(args, package, arch) == "build-pkg"

    # invoked as not pmb install
    args.action = "chroot"
    args.build_pkgs_on_install = False
    assert func(args, package, arch) == "build-pkg"
