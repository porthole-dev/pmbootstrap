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

import os
import pytest
import sys

# Import from parent directory
pmb_src = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/.."))
sys.path.insert(0, pmb_src)
import pmb.chroot.apk_static
import pmb.parse.apkindex
import pmb.helpers.logging
import pmb.helpers.run
import pmb.parse.bootimg


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def pmbootstrap_run(args, parameters, check=True):
    """Execute pmbootstrap.py with a test pmbootstrap.conf."""
    return pmb.helpers.run.user(args, ["./pmbootstrap.py"] + parameters,
                                working_dir=pmb_src, check=check)


def test_crossdirect_rust(args):
    """ Set up buildroot_armhf chroot for building, but remove /usr/bin/rustc.
        Build hello-world-rust for armhf, to verify that it uses
        /native/usr/bin/rustc instead of /usr/bin/rustc. The package has a
        check() function, which makes sure that the built program is actually
        working. """
    pmbootstrap_run(args, ["-y", "zap"])
    pmbootstrap_run(args, ["build_init", "-barmhf"])
    pmbootstrap_run(args, ["chroot", "--add=rust", "-barmhf", "--",
                           "mv", "/usr/bin/rustc", "/usr/bin/rustc_"])
    pmbootstrap_run(args, ["build", "hello-world-rust", "--arch=armhf",
                           "--force"])
    # Make /native/usr/bin/rustc unusuable too, to make the build fail
    pmbootstrap_run(args, ["chroot", "--", "rm", "/usr/bin/rustc"])
    assert pmbootstrap_run(args, ["build", "hello-world-rust", "--arch=armhf",
                                  "--force"], check=False) == 1

    # Make /usr/bin/rustc usable again, to test fallback with qemu
    pmbootstrap_run(args, ["chroot", "-barmhf", "--",
                           "mv", "/usr/bin/rustc_", "/usr/bin/rustc"])
    pmbootstrap_run(args, ["build", "hello-world-rust", "--arch=armhf",
                           "--force"])

    # Clean up
    pmbootstrap_run(args, ["-y", "zap"])
