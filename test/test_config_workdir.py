# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Test pmb/config/workdir.py """
import os
import pytest
import sys
import time

import pmb_test  # noqa
import pmb.config
import pmb.config.workdir


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_chroot_save_date(args, tmpdir, monkeypatch):
    # Override time.time()
    def fake_time():
        return 1234567890.1234
    monkeypatch.setattr(time, "time", fake_time)

    args.work = str(tmpdir)
    func = pmb.config.workdir.chroot_save_date
    func(args, "native")

    expected = "[chroot-init-dates]\nnative = 1234567890\n\n"
    with open(args.work + "/workdir.cfg", "r") as handle:
        assert handle.read() == expected

    # Write again (different code path)
    func(args, "buildroot_armhf")
    expected = ("[chroot-init-dates]\nnative = 1234567890\n"
                "buildroot_armhf = 1234567890\n\n")
    with open(args.work + "/workdir.cfg", "r") as handle:
        assert handle.read() == expected


def test_chroots_outdated(args, tmpdir, monkeypatch):
    args.work = str(tmpdir)

    # Override time.time(): now is "100"
    def fake_time():
        return 100.0
    monkeypatch.setattr(time, "time", fake_time)

    # workdir.cfg does not exist
    func = pmb.config.workdir.chroots_outdated
    assert func(args) is False

    # workdir.cfg is empty file
    with open(args.work + "/workdir.cfg", "w") as handle:
        handle.write("")
    assert func(args) is False

    # Write fake workdir.cfg: native was created at "90"
    with open(args.work + "/workdir.cfg", "w") as handle:
        handle.write("[chroot-init-dates]\nnative = 90\n\n")

    # Outdated (date_outdated: 90)
    monkeypatch.setattr(pmb.config, "chroot_outdated", 10)
    assert func(args) is True

    # Not outdated (date_outdated: 89)
    monkeypatch.setattr(pmb.config, "chroot_outdated", 11)
    assert func(args) is False


def test_clean(args, tmpdir):
    args.work = str(tmpdir)

    # 0. workdir.cfg does not exist
    func = pmb.config.workdir.clean
    assert func(args) is None

    # Write fake workdir.cfg
    cfg_fake = "[chroot-init-dates]\nnative = 1337\n\n"
    with open(args.work + "/workdir.cfg", "w") as handle:
        handle.write(cfg_fake)

    # 1. chroot_native dir exists
    os.makedirs(args.work + "/chroot_native")
    assert func(args) is False

    # workdir.cfg: unchanged
    with open(args.work + "/workdir.cfg", "r") as handle:
        assert handle.read() == cfg_fake

    # 2. chroot_native dir does not exist
    os.rmdir(args.work + "/chroot_native")
    assert func(args) is True

    # workdir.cfg: "native" entry removed
    with open(args.work + "/workdir.cfg", "r") as handle:
        assert handle.read() == "[chroot-init-dates]\n\n"
