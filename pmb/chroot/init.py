# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import enum
import filecmp
from typing import List
from pmb.meta import Cache
from pmb.helpers import logging
import os

import pmb.chroot
import pmb.chroot.binfmt
import pmb.chroot.apk_static
import pmb.config
import pmb.config.workdir
import pmb.helpers.repo
import pmb.helpers.run
import pmb.helpers.other
from pmb.core import Chroot, ChrootType, get_context

cache_chroot_is_outdated: List[str] = []

class UsrMerge(enum.Enum):
    """
    Merge /usr while initializing chroot.
    https://systemd.io/THE_CASE_FOR_THE_USR_MERGE/
    """
    AUTO = 0
    ON = 1
    OFF = 2


def copy_resolv_conf(chroot: Chroot):
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
            pmb.helpers.run.root(["cp", host, resolv_path])
    else:
        pmb.helpers.run.root(["touch", resolv_path])


def mark_in_chroot(chroot: Chroot=Chroot.native()):
    """
    Touch a flag so we can know when we're running in chroot (and
    don't accidentally flash partitions on our host). This marker
    gets removed in pmb.chroot.shutdown (pmbootstrap shutdown).
    """
    in_chroot_file = chroot / "in-pmbootstrap"
    if not in_chroot_file.exists():
        pmb.helpers.run.root(["touch", in_chroot_file])


def init_keys():
    """
    All Alpine and postmarketOS repository keys are shipped with pmbootstrap.
    Copy them into $WORK/config_apk_keys, which gets mounted inside the various
    chroots as /etc/apk/keys.

    This is done before installing any package, so apk can verify APKINDEX
    files of binary repositories even though alpine-keys/postmarketos-keys are
    not installed yet.
    """
    for key in pmb.config.apk_keys_path.glob("*.pub"):
        target = get_context().config.work / "config_apk_keys" / key.name
        if not target.exists():
            # Copy as root, so the resulting files in chroots are owned by root
            pmb.helpers.run.root(["cp", key, target])


def init_usr_merge(chroot: Chroot):
    logging.info(f"({chroot}) merge /usr")
    script = f"{pmb.config.pmb_src}/pmb/data/merge-usr.sh"
    pmb.helpers.run.root(["sh", "-e", script, "CALLED_FROM_PMB",
                                chroot.path])


def warn_if_chroot_is_outdated(chroot: Chroot):
    global cache_chroot_is_outdated

    # Only check / display the warning once per session
    if str(chroot) in cache_chroot_is_outdated:
        return

    if pmb.config.workdir.chroots_outdated(chroot):
        days_warn = int(pmb.config.chroot_outdated / 3600 / 24)
        logging.warning(f"WARNING: Your {chroot} chroot is older than"
                        f" {days_warn} days. Consider running"
                        " 'pmbootstrap zap'.")

    cache_chroot_is_outdated += [str(chroot)]


@Cache("chroot")
def init(chroot: Chroot, usr_merge=UsrMerge.AUTO,
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
    arch = chroot.arch

    config = get_context().config

    pmb.chroot.mount(chroot)
    mark_in_chroot(chroot)
    if (chroot / "bin/sh").is_symlink():
        pmb.config.workdir.chroot_check_channel(chroot)
        copy_resolv_conf(chroot)
        pmb.chroot.apk.update_repository_list(chroot, postmarketos_mirror)
        warn_if_chroot_is_outdated(chroot)
        return

    # Require apk-tools-static
    pmb.chroot.apk_static.init()

    logging.info(f"({chroot}) install alpine-base")

    # Initialize cache
    apk_cache = config.work / f"cache_apk_{arch}"
    pmb.helpers.run.root(["ln", "-s", "-f", "/var/cache/apk",
                                chroot / "etc/apk/cache"])

    # Initialize /etc/apk/keys/, resolv.conf, repositories
    init_keys()
    copy_resolv_conf(chroot)
    pmb.chroot.apk.update_repository_list(chroot, postmarketos_mirror)

    pmb.config.workdir.chroot_save_init(chroot)

    # Install alpine-base
    pmb.helpers.repo.update(arch)
    pkgs = ["alpine-base"]
    # install apk static in the native chroot so we can run it
    # we have a forked apk for systemd and this is the easiest
    # way to install/run it.
    if chroot.type == ChrootType.NATIVE:
        pkgs += ["apk-tools-static"]
    pmb.chroot.apk_static.run(["--root", chroot.path,
                                     "--cache-dir", apk_cache,
                                     "--initdb", "--arch", arch,
                                     "add"] + pkgs)

    # Merge /usr
    if usr_merge is UsrMerge.AUTO and pmb.config.is_systemd_selected(config):
        usr_merge = UsrMerge.ON
    if usr_merge is UsrMerge.ON:
        init_usr_merge(chroot)

    # Building chroots: create "pmos" user, add symlinks to /home/pmos
    if not chroot.type == ChrootType.ROOTFS:
        pmb.chroot.root(["adduser", "-D", "pmos", "-u",
                               pmb.config.chroot_uid_user],
                        chroot)

        # Create the links (with subfolders if necessary)
        for target, link_name in pmb.config.chroot_home_symlinks.items():
            link_dir = os.path.dirname(link_name)
            if not os.path.exists(chroot / link_dir):
                pmb.chroot.user(["mkdir", "-p", link_dir], chroot)
            if not os.path.exists(chroot / target):
                pmb.chroot.root(["mkdir", "-p", target], chroot)
            pmb.chroot.user(["ln", "-s", target, link_name], chroot)
            pmb.chroot.root(["chown", "pmos:pmos", target], chroot)

    # Upgrade packages in the chroot, in case alpine-base, apk, etc. have been
    # built from source with pmbootstrap
    command = ["--no-network", "upgrade", "-a"]

    # Ignore missing repos before initial build (bpo#137)
    if os.getenv("PMB_APK_FORCE_MISSING_REPOSITORIES") == "1":
        command = ["--force-missing-repositories"] + command

    pmb.chroot.root(["apk"] + command, chroot)
