# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.aportgen.core
import pmb.helpers.git
import pmb.helpers.run


def generate(args, pkgname):
    # Copy original aport
    arch = pkgname.split("-")[1]
    upstream = pmb.aportgen.core.get_upstream_aport(args, "binutils")
    pmb.helpers.run.user(args, ["cp", "-r", upstream, args.work + "/aportgen"])

    # Rewrite APKBUILD
    fields = {
        "pkgname": pkgname,
        "pkgdesc": f"Tools necessary to build programs for {arch} targets",
        "arch": pmb.config.arch_native,
    }

    below_header = """
        CTARGET_ARCH=""" + arch + """
        CTARGET="$(arch_to_hostspec $CTARGET_ARCH)"
    """

    pmb.aportgen.core.rewrite(args, pkgname, "main/binutils", fields,
                              "binutils", below_header=below_header)
