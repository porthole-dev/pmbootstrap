# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import Namespace
import multiprocessing
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypedDict, Union

PathString = Union[Path, str]
Env = Dict[str, PathString]

# These types are not definitive / API, they exist to describe the current
# state of things so that we can improve our type hinting coverage and make
# future refactoring efforts easier.

class PartitionLayout(TypedDict):
    kernel: Optional[int]
    boot: int
    reserve: Optional[int]
    root: int

class AportGenEntry(TypedDict):
    prefixes: List[str]
    confirm_overwrite: bool

# Property list generated with:
# $ rg --vimgrep "((^|\s)args\.\w+)" --only-matching | cut -d"." -f3 | sort | uniq
class PmbArgs():
    action_flasher: str
    action_initfs: str
    action_kconfig: str
    action_netboot: str
    add: str
    all: bool
    all_git: str
    all_stable: str
    android_recovery_zip: str
    aports: Path
    _aports_real: str
    arch: str
    as_root: str
    assume_yes: str
    auto: str
    autoinstall: str
    boot_size: str
    build_default_device_arch: str
    build_pkgs_on_install: bool
    buildroot: str
    built: str
    ccache_size: str
    cipher: str
    clear_log: bool
    cmdline: str
    command: str
    config: Path
    cross: bool
    details: bool
    details_to_stdout: bool
    deviceinfo: Dict[str, str]
    deviceinfo_parse_kernel: str
    devices: str
    disk: Path
    dry: str
    efi: str
    envkernel: str
    export_folder: Path
    extra_space: str
    fast: str
    file: str
    filesystem: str
    flash_method: str
    folder: str
    force: str
    fork_alpine: str
    # This is a filthy lie
    from_argparse: "PmbArgs"
    full_disk_encryption: str
    hook: str
    host: str
    hostname: str
    host_qemu: str
    image_size: str
    install_base: str
    install_blockdev: str
    install_cgpt: str
    install_key: bool
    install_local_pkgs: str
    install_recommends: str
    is_default_channel: str
    iter_time: str
    jobs: str
    kconfig_check_details: str
    kernel: str
    keymap: str
    lines: str
    log: Path
    mirror_alpine: str
    mirrors_postmarketos: List[str]
    name: str
    no_depends: str
    no_fde: str
    no_firewall: str
    no_image: str
    non_existing: str
    no_reboot: str
    no_sshd: str
    odin_flashable_tar: str
    offline: bool
    ondev_cp: List[Tuple[str, str]]
    on_device_installer: str
    ondev_no_rootfs: str
    overview: str
    # FIXME (#2324): figure out the args.package vs args.packages situation
    package: str | List[str]
    packages: List[str]
    partition: str
    password: str
    path: Path
    pkgname: str
    pkgname_pkgver_srcurl: str
    port: str
    qemu_audio: str
    qemu_cpu: str
    qemu_display: str
    qemu_gl: str
    qemu_kvm: str
    qemu_redir_stdio: str
    qemu_tablet: str
    qemu_video: str
    recovery_flash_kernel: str
    recovery_install_partition: str
    ref: str
    replace: str
    repository: str
    reset: str
    resume: str
    rootfs: str
    rsync: str
    scripts: str
    second_storage: str
    selected_providers: Dict[str, str]
    sparse: str
    split: str
    src: str
    ssh_keys: str
    strict: str
    sudo_timer: bool
    suffix: str
    systemd: str
    timeout: float
    user: str
    value: str
    verbose: str
    verify: str
    work: Path
    xauth: str
    zap: str


class Config():
    aports: Path = Path(os.path.expanduser("~") +
                        "/.local/var/pmbootstrap/cache_git/pmaports")
    boot_size: int = 256
    build_default_device_arch: bool = False
    build_pkgs_on_install: bool = True
    ccache_size: str = "5G" # yeahhhh this one has a suffix
    device: str = "qemu-amd64"
    extra_packages: str = "none"
    extra_space: int = 0
    hostname: str = ""
    is_default_channel: bool = True
    jobs: str = str(multiprocessing.cpu_count() + 1)
    kernel: str = "stable"
    keymap: str = ""
    locale: str = "en_US.UTF-8"
    # NOTE: mirrors use http by default to leverage caching
    mirror_alpine: str = "http://dl-cdn.alpinelinux.org/alpine/"
    # NOTE: mirrors_postmarketos variable type is supposed to be
    #       comma-separated string, not a python list or any other type!
    mirrors_postmarketos: List[str] = ["http://mirror.postmarketos.org/postmarketos/"]
    qemu_redir_stdio: bool = False
    ssh_key_glob: str = "~/.ssh/id_*.pub"
    ssh_keys: bool = False
    sudo_timer: bool = False
    systemd: str = "default"
    timezone: str = "GMT"
    ui: str = "console"
    ui_extras: bool = False
    user: str = "user"
    work: Path = Path(os.path.expanduser("~") + "/.local/var/pmbootstrap")

    providers: Dict[str, str] = { }

