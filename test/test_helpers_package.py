# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import pytest

import pmb_test  # noqa
import pmb.helpers.logging
import pmb.helpers.package


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_helpers_package_get_pmaports_and_cache(args, monkeypatch):
    """ Test pmb.helpers.package.get(): find in pmaports, use cached result """

    # Fake APKBUILD data
    def stub(args, pkgname, must_exist):
        return {"arch": ["armhf"],
                "depends": ["testdepend"],
                "pkgname": "testpkgname",
                "provides": ["testprovide"],
                "options": [],
                "checkdepends": [],
                "subpackages": {},
                "makedepends": [],
                "pkgver": "1.0",
                "pkgrel": "1"}
    monkeypatch.setattr(pmb.helpers.pmaports, "get", stub)

    package = {"arch": ["armhf"],
               "depends": ["testdepend"],
               "pkgname": "testpkgname",
               "provides": ["testprovide"],
               "version": "1.0-r1"}
    func = pmb.helpers.package.get
    assert func(args, "testpkgname", "armhf") == package

    # Cached result
    monkeypatch.delattr(pmb.helpers.pmaports, "get")
    assert func(args, "testpkgname", "armhf") == package


def test_helpers_package_get_apkindex(args, monkeypatch):
    """ Test pmb.helpers.package.get(): find in apkindex """

    # Fake APKINDEX data
    fake_apkindex_data = {"arch": "armhf",
                          "depends": ["testdepend"],
                          "pkgname": "testpkgname",
                          "provides": ["testprovide"],
                          "version": "1.0-r1"}

    def stub(args, pkgname, arch, must_exist):
        if arch != fake_apkindex_data["arch"]:
            return None
        return fake_apkindex_data
    monkeypatch.setattr(pmb.parse.apkindex, "package", stub)

    # Given arch
    package = {"arch": ["armhf"],
               "depends": ["testdepend"],
               "pkgname": "testpkgname",
               "provides": ["testprovide"],
               "version": "1.0-r1"}
    func = pmb.helpers.package.get
    assert func(args, "testpkgname", "armhf") == package

    # Other arch
    assert func(args, "testpkgname", "x86_64") == package


def test_helpers_package_depends_recurse(args):
    """ Test pmb.helpers.package.depends_recurse() """

    # Put fake data into the pmb.helpers.package.get() cache
    cache = {"a": {False: {"pkgname": "a", "depends": ["b", "c"]}},
             "b": {False: {"pkgname": "b", "depends": []}},
             "c": {False: {"pkgname": "c", "depends": ["d"]}},
             "d": {False: {"pkgname": "d", "depends": ["b"]}}}
    args.cache["pmb.helpers.package.get"]["armhf"] = cache

    # Normal runs
    func = pmb.helpers.package.depends_recurse
    assert func(args, "a", "armhf") == ["a", "b", "c", "d"]
    assert func(args, "d", "armhf") == ["b", "d"]

    # Cached result
    args.cache["pmb.helpers.package.get"]["armhf"] = {}
    assert func(args, "d", "armhf") == ["b", "d"]


def test_helpers_package_check_arch_package(args):
    """ Test pmb.helpers.package.check_arch(): binary = True """
    # Put fake data into the pmb.helpers.package.get() cache
    func = pmb.helpers.package.check_arch
    cache = {"a": {False: {"arch": []}}}
    args.cache["pmb.helpers.package.get"]["armhf"] = cache

    cache["a"][False]["arch"] = ["all !armhf"]
    assert func(args, "a", "armhf") is False

    cache["a"][False]["arch"] = ["all"]
    assert func(args, "a", "armhf") is True

    cache["a"][False]["arch"] = ["noarch"]
    assert func(args, "a", "armhf") is True

    cache["a"][False]["arch"] = ["armhf"]
    assert func(args, "a", "armhf") is True

    cache["a"][False]["arch"] = ["aarch64"]
    assert func(args, "a", "armhf") is False


def test_helpers_package_check_arch_pmaports(args, monkeypatch):
    """ Test pmb.helpers.package.check_arch(): binary = False """
    func = pmb.helpers.package.check_arch
    fake_pmaport = {"arch": []}

    def fake_pmaports_get(args, pkgname, must_exist=False):
        return fake_pmaport
    monkeypatch.setattr(pmb.helpers.pmaports, "get", fake_pmaports_get)

    fake_pmaport["arch"] = ["armhf"]
    assert func(args, "a", "armhf", False) is True

    fake_pmaport["arch"] = ["all", "!armhf"]
    assert func(args, "a", "armhf", False) is False
