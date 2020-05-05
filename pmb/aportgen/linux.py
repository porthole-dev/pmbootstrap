# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.helpers.run
import pmb.aportgen.core
import pmb.parse.apkindex
import pmb.parse.arch


def generate_apkbuild(args, pkgname, deviceinfo, patches):
    device = "-".join(pkgname.split("-")[1:])
    carch = pmb.parse.arch.alpine_to_kernel(deviceinfo["arch"])

    makedepends = "bash bc bison devicepkg-dev flex openssl-dev perl"

    package = """
            downstreamkernel_package "$builddir" "$pkgdir" "$_carch" "$_flavor" "$_outdir\""""

    if deviceinfo["bootimg_qcdt"] == "true":
        makedepends += " dtbtool"

        package += """\n
            # Master DTB (deviceinfo_bootimg_qcdt)
            dtbTool -p scripts/dtc/ -o "$_outdir/arch/$_carch/boot"/dt.img "$_outdir/arch/$_carch/boot/"
            install -Dm644 "$_outdir/arch/$_carch/boot"/dt.img "$pkgdir"/boot/dt.img"""

    patches = ("\n" + " " * 12).join(patches)
    content = f"""\
        # Reference: <https://postmarketos.org/vendorkernel>
        # Kernel config based on: arch/{carch}/configs/(CHANGEME!)

        pkgname={pkgname}
        pkgver=3.x.x
        pkgrel=0
        pkgdesc="{deviceinfo["name"]} kernel fork"
        arch="{deviceinfo["arch"]}"
        _carch="{carch}"
        _flavor="{device}"
        url="https://kernel.org"
        license="GPL-2.0-only"
        options="!strip !check !tracedeps pmb:cross-native"
        makedepends="{makedepends}"

        # Source
        _repository="(CHANGEME!)"
        _commit="ffffffffffffffffffffffffffffffffffffffff"
        _config="config-$_flavor.$arch"
        source="
            $pkgname-$_commit.tar.gz::https://github.com/LineageOS/$_repository/archive/$_commit.tar.gz
            $_config
            {patches}
        "
        builddir="$srcdir/$_repository-$_commit"
        _outdir="out"

        prepare() {{
            default_prepare
            . downstreamkernel_prepare
        }}

        build() {{
            unset LDFLAGS
            make O="$_outdir" ARCH="$_carch" CC="${{CC:-gcc}}" \\
                KBUILD_BUILD_VERSION="$((pkgrel + 1 ))-postmarketOS"
        }}

        package() {{{package}
        }}

        sha512sums="(run 'pmbootstrap checksum {pkgname}' to fill)"
        """

    # Write the file
    with open(args.work + "/aportgen/APKBUILD", "w", encoding="utf-8") as handle:
        for line in content.rstrip().split("\n"):
            handle.write(line[8:].replace(" " * 4, "\t") + "\n")


def generate(args, pkgname):
    device = "-".join(pkgname.split("-")[1:])
    deviceinfo = pmb.parse.deviceinfo(args, device)

    # Symlink commonly used patches
    pmb.helpers.run.user(args, ["mkdir", "-p", args.work + "/aportgen"])
    patches = [
        "gcc7-give-up-on-ilog2-const-optimizations.patch",
        "gcc8-fix-put-user.patch",
        "kernel-use-the-gnu89-standard-explicitly.patch",
    ]
    for patch in patches:
        pmb.helpers.run.user(args, ["ln", "-s",
                                    "../../.shared-patches/linux/" + patch,
                                    args.work + "/aportgen/" + patch])

    generate_apkbuild(args, pkgname, deviceinfo, patches)
