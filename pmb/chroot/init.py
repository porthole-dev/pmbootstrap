# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import enum
import filecmp
from typing import List
from pmb.helpers import logging
import os

import pmb.chroot
import pmb.chroot.apk_static
import pmb.config
import pmb.config.workdir
from pmb.core.types import PmbArgs
import pmb.helpers.repo
import pmb.helpers.run
import pmb.helpers.other
import pmb.parse.arch
from pmb.core import Chroot, ChrootType

cache_chroot_is_outdated: List[str] = []

class UsrMerge(enum.Enum):
    """
    Merge /usr while initializing chroot.
    https://systemd.io/THE_CASE_FOR_THE_USR_MERGE/
    """
    AUTO = 0
    ON = 1
    OFF = 2


def copy_resolv_conf(args: PmbArgs, chroot: Chroot):
    """
    Use pythons super fast file compare function (due to caching)
    and copy the /etc/resolv.conf to the chroot, in case it is
    different from the host.
    If the file doesn't exist, create an empty file with 'touch'.
    """
    host = "/etc/resolv.conf"
    resolv_path = chroot / host
    if os.path.exists(host):
        if not resolv_path.exists() or not filecmp.cmp(host, resolv_path):
            pmb.helpers.run.root(args, ["cp", host, resolv_path])
    else:
        pmb.helpers.run.root(args, ["touch", resolv_path])


def mark_in_chroot(args: PmbArgs, chroot: Chroot=Chroot.native()):
    """
    Touch a flag so we can know when we're running in chroot (and
    don't accidentally flash partitions on our host). This marker
    gets removed in pmb.chroot.shutdown (pmbootstrap shutdown).
    """
    in_chroot_file = chroot / "in-pmbootstrap"
    if not in_chroot_file.exists():
        pmb.helpers.run.root(args, ["touch", in_chroot_file])


def setup_qemu_emulation(args: PmbArgs, chroot: Chroot):
    arch = pmb.parse.arch.from_chroot_suffix(args, chroot)
    if not pmb.parse.arch.cpu_emulation_required(arch):
        return

    arch_qemu = pmb.parse.arch.alpine_to_qemu(arch)

    # mount --bind the qemu-user binary
    pmb.chroot.binfmt.register(args, arch)
    pmb.helpers.mount.bind_file(args, Chroot.native() / f"/usr/bin/qemu-{arch_qemu}",
                                chroot / f"usr/bin/qemu-{arch_qemu}-static",
                                create_folders=True)


def init_keys(args: PmbArgs):
    """
    All Alpine and postmarketOS repository keys are shipped with pmbootstrap.
    Copy them into $WORK/config_apk_keys, which gets mounted inside the various
    chroots as /etc/apk/keys.

    This is done before installing any package, so apk can verify APKINDEX
    files of binary repositories even though alpine-keys/postmarketos-keys are
    not installed yet.
    """
    for key in pmb.config.apk_keys_path.glob("*.pub"):
        target = pmb.config.work / "config_apk_keys" / key.name
        if not target.exists():
            # Copy as root, so the resulting files in chroots are owned by root
            pmb.helpers.run.root(args, ["cp", key, target])


def init_usr_merge(args: PmbArgs, chroot: Chroot):
    logging.info(f"({chroot}) merge /usr")
    script = f"{pmb.config.pmb_src}/pmb/data/merge-usr.sh"
    pmb.helpers.run.root(args, ["sh", "-e", script, "CALLED_FROM_PMB",
                                chroot.path])


def warn_if_chroot_is_outdated(args: PmbArgs, chroot: Chroot):
    global cache_chroot_is_outdated

    # Only check / display the warning once per session
    if str(chroot) in cache_chroot_is_outdated:
        return

    if pmb.config.workdir.chroots_outdated(args, chroot):
        days_warn = int(pmb.config.chroot_outdated / 3600 / 24)
        logging.warning(f"WARNING: Your {chroot} chroot is older than"
                        f" {days_warn} days. Consider running"
                        " 'pmbootstrap zap'.")

    cache_chroot_is_outdated += [str(chroot)]


def init(args: PmbArgs, chroot: Chroot=Chroot.native(), usr_merge=UsrMerge.AUTO,
         postmarketos_mirror=True):
    """
    Initialize a chroot by copying the resolv.conf and updating
    /etc/apk/repositories. If /bin/sh is missing, create the chroot from
    scratch.

    :param usr_merge: set to ON to force having a merged /usr. With AUTO it is
                      only done if the user chose to install systemd in
                      pmbootstrap init.
    :param postmarketos_mirror: add postmarketos mirror URLs
    """
    # When already initialized: just prepare the chroot
    arch = pmb.parse.arch.from_chroot_suffix(args, chroot)

    already_setup = str(chroot) in pmb.helpers.other.cache["pmb.chroot.init"]
    if already_setup:
        # FIXME: drop to debug/verbose later
        logging.debug(f"({chroot}) already initialised")
        return

    pmb.chroot.mount(args, chroot)
    setup_qemu_emulation(args, chroot)
    mark_in_chroot(args, chroot)
    if (chroot / "bin/sh").is_symlink():
        pmb.config.workdir.chroot_check_channel(args, chroot)
        copy_resolv_conf(args, chroot)
        pmb.chroot.apk.update_repository_list(args, chroot, postmarketos_mirror)
        warn_if_chroot_is_outdated(args, chroot)
        pmb.helpers.other.cache["pmb.chroot.init"][str(chroot)] = True
        return

    # Require apk-tools-static
    pmb.chroot.apk_static.init(args)

    logging.info(f"({chroot}) install alpine-base")

    # Initialize cache
    apk_cache = pmb.config.work / f"cache_apk_{arch}"
    pmb.helpers.run.root(args, ["ln", "-s", "-f", "/var/cache/apk",
                                chroot / "etc/apk/cache"])

    # Initialize /etc/apk/keys/, resolv.conf, repositories
    init_keys(args)
    copy_resolv_conf(args, chroot)
    pmb.chroot.apk.update_repository_list(args, chroot, postmarketos_mirror)

    pmb.config.workdir.chroot_save_init(args, chroot)

    # Install alpine-base
    pmb.helpers.repo.update(args, arch)
    pmb.chroot.apk_static.run(args, ["--root", chroot.path,
                                     "--cache-dir", apk_cache,
                                     "--initdb", "--arch", arch,
                                     "add", "alpine-base"])

    # Building chroots: create "pmos" user, add symlinks to /home/pmos
    if not chroot.type == ChrootType.ROOTFS:
        pmb.chroot.root(args, ["adduser", "-D", "pmos", "-u",
                               pmb.config.chroot_uid_user],
                        chroot, auto_init=False)

        # Create the links (with subfolders if necessary)
        for target, link_name in pmb.config.chroot_home_symlinks.items():
            link_dir = os.path.dirname(link_name)
            if not os.path.exists(chroot / link_dir):
                pmb.chroot.user(args, ["mkdir", "-p", link_dir], chroot)
            if not os.path.exists(chroot / target):
                pmb.chroot.root(args, ["mkdir", "-p", target], chroot)
            pmb.chroot.user(args, ["ln", "-s", target, link_name], chroot)
            pmb.chroot.root(args, ["chown", "pmos:pmos", target], chroot)

    # Merge /usr
    if usr_merge is UsrMerge.AUTO and pmb.config.is_systemd_selected(args):
        usr_merge = UsrMerge.ON
    if usr_merge is UsrMerge.ON:
        init_usr_merge(args, chroot)

    # Upgrade packages in the chroot, in case alpine-base, apk, etc. have been
    # built from source with pmbootstrap
    command = ["--no-network", "upgrade", "-a"]

    # Ignore missing repos before initial build (bpo#137)
    if os.getenv("PMB_APK_FORCE_MISSING_REPOSITORIES") == "1":
        command = ["--force-missing-repositories"] + command

    pmb.chroot.root(args, ["apk"] + command, chroot)

    pmb.helpers.other.cache["pmb.chroot.init"][str(chroot)]
