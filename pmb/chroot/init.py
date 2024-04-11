# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import enum
import filecmp
import glob
import logging
import os

import pmb.chroot
import pmb.chroot.apk_static
import pmb.config
import pmb.config.workdir
import pmb.helpers.repo
import pmb.helpers.run
import pmb.parse.arch

cache_chroot_is_outdated = []

class UsrMerge(enum.Enum):
    """
    Merge /usr while initializing chroot.
    https://systemd.io/THE_CASE_FOR_THE_USR_MERGE/
    """
    AUTO = 0
    ON = 1
    OFF = 2


def copy_resolv_conf(args, suffix="native"):
    """
    Use pythons super fast file compare function (due to caching)
    and copy the /etc/resolv.conf to the chroot, in case it is
    different from the host.
    If the file doesn't exist, create an empty file with 'touch'.
    """
    host = "/etc/resolv.conf"
    chroot = f"{args.work}/chroot_{suffix}{host}"
    if os.path.exists(host):
        if not os.path.exists(chroot) or not filecmp.cmp(host, chroot):
            pmb.helpers.run.root(args, ["cp", host, chroot])
    else:
        pmb.helpers.run.root(args, ["touch", chroot])


def mark_in_chroot(args, suffix="native"):
    """
    Touch a flag so we can know when we're running in chroot (and
    don't accidentally flash partitions on our host). This marker
    gets removed in pmb.chroot.shutdown (pmbootstrap shutdown).
    """
    in_chroot_file = f"{args.work}/chroot_{suffix}/in-pmbootstrap"
    if not os.path.exists(in_chroot_file):
        pmb.helpers.run.root(args, ["touch", in_chroot_file])


def setup_qemu_emulation(args, suffix):
    arch = pmb.parse.arch.from_chroot_suffix(args, suffix)
    if not pmb.parse.arch.cpu_emulation_required(arch):
        return

    chroot = f"{args.work}/chroot_{suffix}"
    arch_qemu = pmb.parse.arch.alpine_to_qemu(arch)

    # mount --bind the qemu-user binary
    pmb.chroot.binfmt.register(args, arch)
    pmb.helpers.mount.bind_file(args, f"{args.work}/chroot_native"
                                      f"/usr/bin/qemu-{arch_qemu}",
                                f"{chroot}/usr/bin/qemu-{arch_qemu}-static",
                                create_folders=True)


def init_keys(args):
    """
    All Alpine and postmarketOS repository keys are shipped with pmbootstrap.
    Copy them into $WORK/config_apk_keys, which gets mounted inside the various
    chroots as /etc/apk/keys.

    This is done before installing any package, so apk can verify APKINDEX
    files of binary repositories even though alpine-keys/postmarketos-keys are
    not installed yet.
    """
    for key in glob.glob(f"{pmb.config.apk_keys_path}/*.pub"):
        target = f"{args.work}/config_apk_keys/{os.path.basename(key)}"
        if not os.path.exists(target):
            # Copy as root, so the resulting files in chroots are owned by root
            pmb.helpers.run.root(args, ["cp", key, target])


def init_usr_merge(args, suffix):
    logging.info(f"({suffix}) merge /usr")
    script = f"{pmb.config.pmb_src}/pmb/data/merge-usr.sh"
    pmb.helpers.run.root(args, ["sh", "-e", script, "CALLED_FROM_PMB",
                                f"{args.work}/chroot_{suffix}"])


def warn_if_chroot_is_outdated(args, suffix):
    global cache_chroot_is_outdated

    # Only check / display the warning once per session
    if suffix in cache_chroot_is_outdated:
        return

    if pmb.config.workdir.chroots_outdated(args, suffix):
        days_warn = int(pmb.config.chroot_outdated / 3600 / 24)
        logging.warning(f"WARNING: Your {suffix} chroot is older than"
                        f" {days_warn} days. Consider running"
                        " 'pmbootstrap zap'.")

    cache_chroot_is_outdated += [suffix]


def init(args, suffix="native", usr_merge=UsrMerge.AUTO,
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
    chroot = f"{args.work}/chroot_{suffix}"
    arch = pmb.parse.arch.from_chroot_suffix(args, suffix)

    pmb.chroot.mount(args, suffix)
    setup_qemu_emulation(args, suffix)
    mark_in_chroot(args, suffix)
    if os.path.islink(f"{chroot}/bin/sh"):
        pmb.config.workdir.chroot_check_channel(args, suffix)
        copy_resolv_conf(args, suffix)
        pmb.chroot.apk.update_repository_list(args, suffix, postmarketos_mirror)
        warn_if_chroot_is_outdated(args, suffix)
        return

    # Require apk-tools-static
    pmb.chroot.apk_static.init(args)

    logging.info(f"({suffix}) install alpine-base")

    # Initialize cache
    apk_cache = f"{args.work}/cache_apk_{arch}"
    pmb.helpers.run.root(args, ["ln", "-s", "-f", "/var/cache/apk",
                                f"{chroot}/etc/apk/cache"])

    # Initialize /etc/apk/keys/, resolv.conf, repositories
    init_keys(args)
    copy_resolv_conf(args, suffix)
    pmb.chroot.apk.update_repository_list(args, suffix, postmarketos_mirror)

    pmb.config.workdir.chroot_save_init(args, suffix)

    # Install alpine-base
    pmb.helpers.repo.update(args, arch)
    pmb.chroot.apk_static.run(args, ["--root", chroot,
                                     "--cache-dir", apk_cache,
                                     "--initdb", "--arch", arch,
                                     "add", "alpine-base"])

    # Building chroots: create "pmos" user, add symlinks to /home/pmos
    if not suffix.startswith("rootfs_"):
        pmb.chroot.root(args, ["adduser", "-D", "pmos", "-u",
                               pmb.config.chroot_uid_user],
                        suffix, auto_init=False)

        # Create the links (with subfolders if necessary)
        for target, link_name in pmb.config.chroot_home_symlinks.items():
            link_dir = os.path.dirname(link_name)
            if not os.path.exists(f"{chroot}{link_dir}"):
                pmb.chroot.user(args, ["mkdir", "-p", link_dir], suffix)
            if not os.path.exists(f"{chroot}{target}"):
                pmb.chroot.root(args, ["mkdir", "-p", target], suffix)
            pmb.chroot.user(args, ["ln", "-s", target, link_name], suffix)
            pmb.chroot.root(args, ["chown", "pmos:pmos", target], suffix)

    # Merge /usr
    if usr_merge is UsrMerge.AUTO and pmb.config.is_systemd_selected(args):
        usr_merge = UsrMerge.ON
    if usr_merge is UsrMerge.ON:
        init_usr_merge(args, suffix)

    # Upgrade packages in the chroot, in case alpine-base, apk, etc. have been
    # built from source with pmbootstrap
    pmb.chroot.root(args, ["apk", "--no-network", "upgrade", "-a"], suffix)
