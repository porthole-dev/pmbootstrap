# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from pmb.core.context import get_context
from pmb.helpers.args import init as init_args
from pmb.types import PmbArgs


@pytest.mark.parametrize("ignore_depends", [False, True])
def test_build_ignore_depends_reaches_context(
    config_file: Path, mock_context: None, logfile: Path, ignore_depends: bool
) -> None:
    args = PmbArgs()
    args.config = config_file
    args.aports = None
    args.timeout = 900
    args.details_to_stdout = False
    args.quiet = False
    args.verbose = True
    args.offline = False
    args.action = "init"
    args.cross = False
    args.ccache = True
    args.log = logfile
    args.ignore_depends = ignore_depends

    init_args(args)

    assert get_context().ignore_depends is ignore_depends
