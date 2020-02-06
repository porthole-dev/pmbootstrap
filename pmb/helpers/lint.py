"""
Copyright 2020 Danct12 <danct12@disroot.org>

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
import logging

import pmb.chroot
import pmb.chroot.apk
import pmb.build
import pmb.helpers.run
import pmb.helpers.pmaports


def check(args, pkgname):
    pmb.chroot.apk.install(args, ["atools"])

    # Run apkbuild-lint on copy of pmaport in chroot
    pmb.build.init(args)
    pmb.build.copy_to_buildpath(args, pkgname)
    logging.info("(native) linting " + pkgname + " with apkbuild-lint")
    pmb.chroot.user(args, ["apkbuild-lint", "APKBUILD"],
                    check=False, output="stdout",
                    working_dir="/home/pmos/build")
