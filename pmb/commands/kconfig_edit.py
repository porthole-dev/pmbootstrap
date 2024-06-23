# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from pmb import commands
import pmb.build
import pmb.helpers.args


class KConfigEdit(commands.Command):
    pkgname: str
    use_oldconfig: bool

    def __init__(self, pkgname, use_oldconfig):
        self.pkgname = pkgname
        self.use_oldconfig = use_oldconfig
        pass

    def run(self):
        args = pmb.helpers.args.please_i_really_need_args()
        pmb.build.menuconfig(args, self.pkgname, self.use_oldconfig)
