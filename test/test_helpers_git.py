"""
Copyright 2019 Oliver Smith

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
import sys
import pytest

# Import from parent directory
sys.path.insert(0, os.path.realpath(
    os.path.join(os.path.dirname(__file__) + "/..")))
import pmb.helpers.git
import pmb.helpers.logging


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_get_path(args):
    func = pmb.helpers.git.get_path
    args.work = "/wrk"
    args.aports = "/tmp/pmaports"

    assert func(args, "aports_upstream") == "/wrk/cache_git/aports_upstream"
    assert func(args, "pmaports") == "/tmp/pmaports"
