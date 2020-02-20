# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
import sys

import pmb_test
import pmb_test.const
import pmb.aportgen.device
import pmb.config
import pmb.config.init
import pmb.helpers.logging
import pmb.install._install


@pytest.fixture
def args(tmpdir, request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_get_nonfree_packages(args):
    args.aports = pmb_test.const.testdata + "/init_questions_device/aports"
    func = pmb.install._install.get_nonfree_packages

    # Device without any non-free subpackages
    args.nonfree_firmware = True
    args.nonfree_userland = True
    assert func(args, "lg-mako") == []

    # Device with non-free firmware and userland
    device = "nonfree-firmware-and-userland"
    assert func(args, device) == ["device-" + device + "-nonfree-firmware",
                                  "device-" + device + "-nonfree-userland"]

    # Device with non-free userland
    device = "nonfree-userland"
    assert func(args, device) == ["device-" + device + "-nonfree-userland"]

    # Device with non-free userland (but user disabled it init)
    args.nonfree_userland = False
    assert func(args, device) == []
