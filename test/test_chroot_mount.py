# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Test pmb/chroot/mount.py """
import os
from pmb.core.types import PmbArgs
import pytest
import sys

import pmb_test  # noqa
import pmb.chroot
from pmb.core import Chroot

@pytest.fixture
def args(tmpdir, request):
    import pmb.parse
    sys.argv = ["pmbootstrap", "init"]
    args = pmb.parse.arguments()
    args.log = pmb.config.work / "log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(pmb.helpers.logging.logfd.close)
    return args


def test_chroot_mount(args: PmbArgs):
    chroot = Chroot.native()
    mnt_dir = chroot / "mnt/pmbootstrap"

    # Run something in the chroot to have the dirs created
    pmb.chroot.root(args, ["true"])
    assert mnt_dir.exists()
    assert (mnt_dir / "packages").exists()

    # Umount everything, like in pmb.install.install_system_image
    pmb.helpers.mount.umount_all(chroot.path)

    # Remove all /mnt/pmbootstrap dirs
    pmb.chroot.remove_mnt_pmbootstrap(args, chroot)
    assert not mnt_dir.exists()

    # Run again: it should not crash
    pmb.chroot.remove_mnt_pmbootstrap(args, chroot)
