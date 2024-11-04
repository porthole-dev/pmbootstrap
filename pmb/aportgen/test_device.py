from pmb.types import Bootimg
import pytest

from .device import generate_deviceinfo_fastboot_content

# Test case name -> (input, expected substrings, !expected substrings)
test_data: dict[str, tuple[Bootimg | None, list[str], list[str]]] = {
    "none": (None, ['kernel_cmdline=""', 'flash_pagesize="2048"'], []),
    "header_v0": (
        Bootimg(
            cmdline="beep boop",
            header_version="0",
            qcdt="false",
            base="0x80000000",
            kernel_offset="0x8000",
            tags_offset="0x100",
            qcdt_type=None,
            dtb_offset=None,
            dtb_second="",
            pagesize="2048",
            ramdisk_offset="",
            second_offset="",
            mtk_label_kernel="",
            mtk_label_ramdisk="",
        ),
        [
            'kernel_cmdline="beep boop"',
            'flash_pagesize="2048"',
            'flash_offset_base="0x80000000"',
            'flash_offset_kernel="0x8000"',
            'flash_offset_tags="0x100"',
        ],
        [],
    ),
    "header_v2": (
        Bootimg(
            cmdline="console=ttyMSM0,115200n8",
            header_version="2",
            qcdt="false",
            base="0x80000000",
            kernel_offset="",
            tags_offset="",
            qcdt_type=None,
            dtb_offset="0x101f00000",
            dtb_second="",
            pagesize="2048",
            ramdisk_offset="",
            second_offset="",
            mtk_label_kernel="",
            mtk_label_ramdisk="",
        ),
        [
            'kernel_cmdline="console=ttyMSM0,115200n8"',
            'flash_pagesize="2048"',
            'append_dtb="false"',
            'flash_offset_dtb="0x101f00000"',
        ],
        [
            "qcdt",
        ],
    ),
    "header_v3": (
        Bootimg(
            cmdline="console=ttyMSM0,115200n8",
            header_version="3",
            qcdt="false",
            base="",
            kernel_offset="",
            tags_offset="",
            qcdt_type=None,
            dtb_offset="",
            dtb_second="",
            pagesize="4096",
            ramdisk_offset="",
            second_offset="",
            mtk_label_kernel="",
            mtk_label_ramdisk="",
        ),
        [
            'kernel_cmdline="console=ttyMSM0,115200n8"',
            'flash_pagesize="4096"',
        ],
        [
            "flash_offset_base",
        ],
    ),
}


@pytest.mark.parametrize("case", [*test_data.keys()])
def test_deviceinfo_fastboot(case):
    bootimg = test_data[case][0]
    expected_substrings = test_data[case][1]
    unexpected_substrings = test_data[case][2]
    content = generate_deviceinfo_fastboot_content(bootimg)

    print(content)
    for substring in expected_substrings:
        assert substring in content, f"Expected substring not found: {substring}"

    for substring in unexpected_substrings:
        assert substring not in content, f"Unexpected substring found: {substring}"
