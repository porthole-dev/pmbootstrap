import pytest

from .arch import Arch
from .context import get_context
from .chroot import Chroot, ChrootType


def test_valid_chroots(pmb_args, mock_devices_find_path):
    """Test that Chroot objects work as expected"""

    work = get_context().config.work

    chroot = Chroot.native()
    assert chroot.type == ChrootType.NATIVE
    assert chroot.name == ""
    assert chroot.arch in Arch.supported()
    assert not chroot.exists()  # Shouldn't be created
    assert chroot.path == work / "chroot_native"
    assert str(chroot) == "native"

    chroot = Chroot.buildroot(Arch.aarch64)
    assert chroot.type == ChrootType.BUILDROOT
    assert chroot.name == "aarch64"
    assert chroot.arch == Arch.aarch64
    assert not chroot.exists()  # Shouldn't be created
    assert chroot.path == work / "chroot_buildroot_aarch64"
    assert str(chroot) == "buildroot_aarch64"

    # FIXME: implicily assumes that we're mocking the qemu-amd64 deviceinfo
    chroot = Chroot(ChrootType.ROOTFS, "qemu-amd64")
    assert chroot.type == ChrootType.ROOTFS
    assert chroot.name == "qemu-amd64"
    assert chroot.arch == Arch.x86_64
    assert not chroot.exists()  # Shouldn't be created
    assert chroot.path == work / "chroot_rootfs_qemu-amd64"
    assert str(chroot) == "rootfs_qemu-amd64"


# mypy: ignore-errors
def test_invalid_chroots(pmb_args):
    """Test that we can't create invalid chroots."""

    with pytest.raises(ValueError) as excinfo:
        Chroot(ChrootType.BUILDROOT, "BAD_ARCH")
    assert (
        str(excinfo.value)
        == "Invalid architecture: 'BAD_ARCH', expected something like: aarch64, armhf, armv7, ppc64le, riscv64, x86, x86_64"
    )

    with pytest.raises(ValueError) as excinfo:
        Chroot(ChrootType.NATIVE, "aarch64")
    assert str(excinfo.value) == "The native suffix can't have a name but got: 'aarch64'"

    with pytest.raises(ValueError) as excinfo:
        Chroot("beep boop")
    assert str(excinfo.value) == "Invalid chroot type: 'beep boop'"

    with pytest.raises(ValueError) as excinfo:
        Chroot(5)
    assert str(excinfo.value) == "Invalid chroot type: '5'"


@pytest.mark.xfail
def test_untested_chroots():
    # IMAGE type is untested, name should be a valid path in this case
    tested_chroot_types = [
        ChrootType.ROOTFS,
        ChrootType.BUILDROOT,
        ChrootType.NATIVE,
        ChrootType.INSTALLER,
    ]
    for ct in ChrootType:
        if ct not in tested_chroot_types:
            raise ValueError(f"ChrootType {ct} is untested!")
