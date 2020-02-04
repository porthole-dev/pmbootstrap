# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Test pmb/helpers/status.py """
import pytest
import sys

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


def test_pmbootstrap_status(args, tmpdir):
    """ High level testing of 'pmbootstrap status': run it twice, once with
        a fine workdir, and once where one check is failing. """
    # Prepare empty workdir
    work = str(tmpdir)
    with open(work + "/version", "w") as handle:
        handle.write(str(pmb.config.work_version))

    # "pmbootstrap status" succeeds (pmb.helpers.run.user verifies exit 0)
    pmbootstrap = pmb.config.pmb_src + "/pmbootstrap.py"
    pmb.helpers.run.user(args, [pmbootstrap, "-w", work, "status",
                                "--details"])

    # Mark chroot_native as outdated
    with open(work + "/workdir.cfg", "w") as handle:
        handle.write("[chroot-init-dates]\nnative = 1234\n")

    # "pmbootstrap status" fails
    ret = pmb.helpers.run.user(args, [pmbootstrap, "-w", work, "status"],
                               check=False)
    assert ret == 1
