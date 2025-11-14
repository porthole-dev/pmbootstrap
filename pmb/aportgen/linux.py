# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.aportgen.device import ask_for_architecture
from pmb.core.context import get_context
from pmb.helpers.exceptions import NonBugError
from pmb.parse.deviceinfo import Deviceinfo
import pmb.helpers.run
import pmb.parse.apkindex


def generate_apkbuild(
    pkgname: str,
    deviceinfo: Deviceinfo | None,
    patches: list[str],
    device_category: pmb.helpers.devices.DeviceCategory,
) -> None:
    device = "-".join(pkgname.split("-")[1:])
    arch = deviceinfo.arch if deviceinfo else ask_for_architecture()
    carch = arch.kernel_dir()

    makedepends = [
        "bash",
        "bc",
        "bison",
        "devicepkg-dev",
        "findutils",
        "flex",
        "openssl-dev",
        "perl",
    ]

    # Downstream kernel
    if device_category == pmb.helpers.devices.DeviceCategory.DOWNSTREAM:
        reference_url = "https://postmarketos.org/vendorkernel"

        outdir = '_outdir="out"\n'

        prepare = """
            default_prepare
            . downstreamkernel_prepare"""

        build = """
            unset LDFLAGS
            make O="$_outdir" ARCH="$_carch" CC="${CC:-gcc}" \\
                KBUILD_BUILD_VERSION="$((pkgrel + 1 ))-postmarketOS\""""

        package = """
            downstreamkernel_package "$builddir" "$pkgdir" "$_carch\" \\
                "$_flavor" "$_outdir\""""

        if deviceinfo:
            has_dtb = deviceinfo.header_version and deviceinfo.header_version >= 2
        else:
            has_dtb = pmb.helpers.cli.confirm(
                "Does the device use DTBs?", default=True, no_assumptions=True
            )

        if has_dtb:
            package += """
            make dtbs_install O="$_outdir" ARCH="$_carch" \\
                INSTALL_DTBS_PATH="$pkgdir\"/boot/dtbs"""

        if deviceinfo:
            has_qcdt = deviceinfo.bootimg_qcdt == "true"
        else:
            has_qcdt = pmb.helpers.cli.confirm(
                "Does the device use QCDT (see <https://wiki.postmarketos.org/wiki/QCDT>)?",
                default=False,
                no_assumptions=True,
            )

        if has_qcdt:
            build += """\n
            # Master DTB (deviceinfo_bootimg_qcdt)"""
            vendors = ["spreadtrum", "exynos", "other"]
            soc_vendor = pmb.helpers.cli.ask("SoC vendor", vendors, vendors[-1], complete=vendors)
            if soc_vendor == "spreadtrum":
                makedepends.append("dtbtool-sprd")
                build += """
            dtbTool-sprd -p "$_outdir/scripts/dtc/" \\
                -o "$_outdir/arch/$_carch/boot"/dt.img \\
                "$_outdir/arch/$_carch/boot/dts/\""""
            elif soc_vendor == "exynos":
                codename = "-".join(pkgname.split("-")[2:])
                makedepends.append("dtbtool-exynos")
                build += """
            dtbTool-exynos -o "$_outdir/arch/$_carch/boot"/dt.img \\
                $(find "$_outdir/arch/$_carch/boot/dts/\""""
                build += f" -name *{codename}*.dtb)"
            else:
                makedepends.append("dtbtool")
                build += """
            dtbTool -o "$_outdir/arch/$_carch/boot"/dt.img \\
                "$_outdir/arch/$_carch/boot/\""""
            package += """
            install -Dm644 "$_outdir/arch/$_carch/boot"/dt.img \\
                "$pkgdir"/boot/dt.img"""

    # Mainline kernel
    else:
        reference_url = None

        # Add LLVM dependencies
        makedepends += ["clang", "lld", "llvm"]

        outdir = ""

        prepare = """
            default_prepare
            cp -v "$srcdir/$_config" .config"""

        build = """
            unset LDFLAGS
            make ARCH="$_carch" LLVM=1 \\
                KBUILD_BUILD_VERSION="$((pkgrel + 1 ))-postmarketOS\""""

        package = """
            mkdir -p "$pkgdir"/boot
            make zinstall modules_install dtbs_install \\
                ARCH="$_carch" \\
                LLVM=1 \\
                INSTALL_MOD_STRIP=1 \\
                INSTALL_PATH="$pkgdir"/boot \\
                INSTALL_MOD_PATH="$pkgdir" \\
                INSTALL_DTBS_PATH="$pkgdir/boot/dtbs"

            install -D "$builddir"/include/config/kernel.release \\
                "$pkgdir/usr/share/kernel/$_flavor/kernel.release\""""

    makedepends.sort()
    makedepends_fmt = ("\n" + " " * 12).join(makedepends)
    patches_str = ("\n" + " " * 12).join(patches)
    reference_str = " " * 8 + f"# Reference: <{reference_url}>\n" if reference_url else ""
    content = f"""{reference_str}\
        # Kernel config based on: arch/{carch}/configs/(CHANGEME!)

        maintainer=""
        pkgname={pkgname}
        pkgver=3.x.x
        pkgrel=0
        pkgdesc="{deviceinfo.name if deviceinfo else "(CHANGEME!)"} kernel fork"
        arch="{arch}"
        _carch="{carch}"
        _flavor="{device}"
        url="https://kernel.org"
        license="GPL-2.0-only"
        options="!strip !check !tracedeps pmb:cross-native"
        makedepends="
            {makedepends_fmt}
        "

        # Source
        _repository="(CHANGEME!)"
        _commit="ffffffffffffffffffffffffffffffffffffffff"
        _config="config-$_flavor.$arch"
        source="
            $pkgname-$_commit.tar.gz::https://github.com/(CHANGEME!)/$_repository/archive/$_commit.tar.gz
            $_config
            {patches_str}
        "
        builddir="$srcdir/$_repository-$_commit"
        {outdir}
        prepare() {{{prepare}
        }}

        build() {{{build}
        }}

        package() {{{package}
        }}

        sha512sums="(run 'pmbootstrap checksum {pkgname}' to fill)"
        """

    # Write the file
    with (get_context().config.work / "aportgen/APKBUILD").open("w", encoding="utf-8") as hndl:
        for line in content.rstrip().split("\n"):
            hndl.write(line[8:].replace(" " * 4, "\t") + "\n")


def generate(pkgname: str, device_category: pmb.helpers.devices.DeviceCategory) -> None:
    device = "-".join(pkgname.split("-")[1:])
    try:
        deviceinfo = pmb.parse.deviceinfo(device)
    except NonBugError:  # device not found
        deviceinfo = None
    work = get_context().config.work

    pmb.helpers.run.user(["mkdir", "-p", work / "aportgen"])

    # Symlink commonly used patches
    if device_category == pmb.helpers.devices.DeviceCategory.DOWNSTREAM:
        patches = [
            "gcc7-give-up-on-ilog2-const-optimizations.patch",
            "gcc8-fix-put-user.patch",
            "gcc10-extern_YYLOC_global_declaration.patch",
            "kernel-use-the-gnu89-standard-explicitly.patch",
        ]
        for patch in patches:
            pmb.helpers.run.user(
                ["ln", "-s", "../../.shared-patches/linux/" + patch, (work / "aportgen" / patch)]
            )
    else:
        patches = []

    generate_apkbuild(pkgname, deviceinfo, patches, device_category)
