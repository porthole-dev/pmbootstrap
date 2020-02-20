"""
Copyright 2020 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
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
