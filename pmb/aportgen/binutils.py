# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.aportgen.core
import pmb.helpers.git
import pmb.helpers.run


def generate(args, pkgname):
    # Copy original aport
    arch = pkgname.split("-")[1]
    upstream = pmb.aportgen.core.get_upstream_aport(args, "binutils")
    pmb.helpers.run.user(args, ["cp", "-r", upstream, args.work + "/aportgen"])

    # Architectures to build this package for
    arches = list(pmb.config.build_device_architectures)
    arches.remove(arch)

    # Rewrite APKBUILD
    fields = {
        "pkgname": pkgname,
        "pkgdesc": "Tools necessary to build programs for " + arch + " targets",
        "arch": " ".join(arches),
        "makedepends_build": "",
        "makedepends_host": "",
        "makedepends": "gettext libtool autoconf automake bison texinfo",
        "subpackages": "",
    }

    replace_functions = {
        "build": """
            _target="$(arch_to_hostspec """ + arch + """)"
            "$builddir"/configure \\
                --build="$CBUILD" \\
                --target=$_target \\
                --with-lib-path=/usr/lib \\
                --prefix=/usr \\
                --with-sysroot=/usr/$_target \\
                --enable-ld=default \\
                --enable-gold=yes \\
                --enable-plugins \\
                --enable-deterministic-archives \\
                --disable-multilib \\
                --disable-werror \\
                --disable-nls
            make
        """,
        "package": """
            make install DESTDIR="$pkgdir"

            # remove man, info folders
            rm -rf "$pkgdir"/usr/share
        """,
        "libs": None,
        "gold": None,
    }

    pmb.aportgen.core.rewrite(args, pkgname, "main/binutils", fields,
                              "binutils", replace_functions, remove_indent=8)
