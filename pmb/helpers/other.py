# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.core.context import get_context
from pmb.core.arch import Arch
from pmb.helpers import logging
import os
from pathlib import Path
import re
import pmb.chroot
import pmb.config
import pmb.config.init
import pmb.helpers.pmaports
import pmb.helpers.run
from typing import Any


def folder_size(path: Path):
    """Run `du` to calculate the size of a folder.

    (this is less code and faster than doing the same task in pure Python)
    This result is only approximatelly right, but good enough for pmbootstrap's use case (#760).

    :returns: folder size in kilobytes
    """
    output = pmb.helpers.run.root(["du", "-ks", path], output_return=True)

    # Only look at last line to filter out sudo garbage (#1766)
    last_line = output.split("\n")[-2]

    ret = int(last_line.split("\t")[0])
    return ret


def check_grsec():
    """Check if the current kernel is based on the grsec patchset.

    Also check if the chroot_deny_chmod option is enabled.
    Raise an exception in that case, with a link to the issue. Otherwise, do nothing.
    """
    path = "/proc/sys/kernel/grsecurity/chroot_deny_chmod"
    if not os.path.exists(path):
        return

    raise RuntimeError(
        "You're running a kernel based on the grsec" " patchset. This is not supported."
    )


def check_binfmt_misc():
    """Check if the 'binfmt_misc' module is loaded.

    This is done by checking, if /proc/sys/fs/binfmt_misc/ exists.
    If it exists, then do nothing.
    Otherwise, load the module and mount binfmt_misc.
    If that fails as well, raise an exception pointing the user to the wiki.
    """
    path = "/proc/sys/fs/binfmt_misc/status"
    if os.path.exists(path):
        return

    # check=False: this might be built-in instead of being a module
    pmb.helpers.run.root(["modprobe", "binfmt_misc"], check=False)

    # check=False: we check it below and print a more helpful message on error
    pmb.helpers.run.root(
        ["mount", "-t", "binfmt_misc", "none", "/proc/sys/fs/binfmt_misc"], check=False
    )

    if not os.path.exists(path):
        link = "https://postmarketos.org/binfmt_misc"
        raise RuntimeError(f"Failed to set up binfmt_misc, see: {link}")


def migrate_success(work: Path, version):
    logging.info("Migration to version " + str(version) + " done")
    with open(work / "version", "w") as handle:
        handle.write(str(version) + "\n")


def migrate_work_folder():
    # Read current version
    context = get_context()
    current = 0
    path = context.config.work / "version"
    if os.path.exists(path):
        with open(path) as f:
            current = int(f.read().rstrip())

    # Compare version, print warning or do nothing
    required = pmb.config.work_version
    if current == required:
        return
    logging.info(
        "WARNING: Your work folder version needs to be migrated"
        " (from version " + str(current) + " to " + str(required) + ")!"
    )

    # 0 => 1
    if current == 0:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* Building chroots have a different username (#709)")
        logging.info("Migration will do the following:")
        logging.info("* Zap your chroots")
        logging.info(f"* Adjust '{context.config.work / 'config_abuild/abuild.conf'}'")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Zap and update abuild.conf
        pmb.chroot.zap(False)
        conf = context.config.work / "config_abuild/abuild.conf"
        if os.path.exists(conf):
            pmb.helpers.run.root(["sed", "-i", "s./home/user/./home/pmos/.g", conf])
        # Update version file
        migrate_success(context.config.work, 1)
        current = 1

    # 1 => 2
    if current == 1:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* Fix: cache_distfiles was writable for everyone")
        logging.info("Migration will do the following:")
        logging.info(f"* Fix permissions of '{context.config.work / 'cache_distfiles'}'")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Fix permissions
        dir = "/var/cache/distfiles"
        for cmd in [
            ["chown", "-R", "root:abuild", dir],
            ["chmod", "-R", "664", dir],
            ["chmod", "a+X", dir],
        ]:
            pmb.chroot.root(cmd)
        migrate_success(context.config.work, 2)
        current = 2

    if current == 2:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* Device chroots have a different user UID (#1576)")
        logging.info("Migration will do the following:")
        logging.info("* Zap your chroots")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Zap chroots
        pmb.chroot.zap(False)

        # Update version file
        migrate_success(context.config.work, 3)
        current = 3

    if current == 3:
        # Ask for confirmation
        path = context.config.work / "cache_git"
        logging.info("Changelog:")
        logging.info("* pmbootstrap clones repositories with host system's")
        logging.info("  'git' instead of using it from an Alpine chroot")
        logging.info("Migration will do the following:")
        logging.info("* Check if 'git' is installed")
        logging.info(f"* Change ownership to your user: {path}")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Require git, set cache_git ownership
        pmb.config.init.require_programs()
        if os.path.exists(path):
            uid_gid = f"{os.getuid()}:{os.getgid()}"
            pmb.helpers.run.root(["chown", "-R", uid_gid, path])
        else:
            os.makedirs(path, 0o700, True)

        # Update version file
        migrate_success(context.config.work, 4)
        current = 4

    if current == 4:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* packages built by pmbootstrap are in a channel subdir")
        logging.info("Migration will do the following:")
        logging.info("* Move existing packages to edge subdir (if any)")
        logging.info("* Zap your chroots")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Zap chroots
        pmb.chroot.zap(False)

        # Move packages to edge subdir
        edge_path = context.config.work / "packages/edge"
        pmb.helpers.run.root(["mkdir", "-p", edge_path])
        for arch in Arch.supported():
            old_path = context.config.work / "packages" / arch
            new_path = edge_path / arch
            if old_path.exists():
                if new_path.exists():
                    raise RuntimeError(
                        f"Won't move '{old_path}' to"
                        f" '{new_path}', destination already"
                        " exists! Consider 'pmbootstrap zap -p'"
                        f" to delete '{context.config.work}/packages'."
                    )
                pmb.helpers.run.root(["mv", old_path, new_path])
        pmb.helpers.run.root(["chown", pmb.config.chroot_uid_user, edge_path])

        # Update version file
        migrate_success(context.config.work, 5)
        current = 5

    if current == 5:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* besides edge, pmaports channels have the same name")
        logging.info("  as the branch now (pmbootstrap#2015)")
        logging.info("Migration will do the following:")
        logging.info("* Zap your chroots")
        logging.info("* Adjust subdirs of your locally built packages dir:")
        logging.info(f"  {context.config.work}/packages")
        logging.info("  stable => v20.05")
        logging.info("  stable-next => v21.03")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Zap chroots to avoid potential "ERROR: Chroot 'native' was created
        # for the 'stable' channel, but you are on the 'v20.05' channel now."
        pmb.chroot.zap(False)

        # Migrate
        packages_dir = f"{context.config.work}/packages"
        for old, new in pmb.config.pmaports_channels_legacy.items():
            if os.path.exists(f"{packages_dir}/{old}"):
                pmb.helpers.run.root(["mv", old, new], packages_dir)

        # Update version file
        migrate_success(context.config.work, 6)
        current = 6

    if current == 6:
        # Ask for confirmation
        logging.info("Changelog:")
        logging.info("* Major refactor for pmb 3.0.0")
        logging.info("Migration will do the following:")
        logging.info("* Zap your chroots")
        if not pmb.helpers.cli.confirm():
            raise RuntimeError("Aborted.")

        # Zap chroots
        pmb.chroot.zap(False)

        # Update version file
        migrate_success(context.config.work, 7)
        current = 7

    # Can't migrate, user must delete it
    if current != required:
        raise RuntimeError(
            "Sorry, we can't migrate that automatically. Please"
            " run 'pmbootstrap shutdown', then delete your"
            " current work folder manually ('sudo rm -rf "
            f"{context.config.work}') and start over with 'pmbootstrap"
            " init'. All your binary packages and caches will"
            " be lost."
        )


def normalize_hostname(hostname: str) -> str:
    """Fixup default hostnames so that they don't fail validate_hostname()

    This should not be called on user-chosen hostnames as those should fail
    """
    # Truncate length
    if len(hostname) > 63:
        hostname = hostname[:63]

    # Replace underscores with dashes
    if "_" in hostname:
        hostname = hostname.replace("_", "-")

    # We shouldn't have to fix the rest of the regex because the APKBUILDs'
    # device names shouldn't have any more invalid characters

    return hostname


def validate_hostname(hostname):
    """Check whether the string is a valid hostname.

    Check is performed according to
    <http://en.wikipedia.org/wiki/Hostname#Restrictions_on_valid_host_names>
    """
    # Check length
    if len(hostname) > 63:
        logging.fatal("ERROR: Hostname '" + hostname + "' is too long.")
        return False

    # Check that it only contains valid chars
    if not re.match(r"^[0-9a-z-\.]*$", hostname):
        logging.fatal(
            "ERROR: Hostname must only contain letters (a-z),"
            " digits (0-9), minus signs (-), or periods (.)"
        )
        return False

    # Check that doesn't begin or end with a minus sign or period
    if re.search(r"^-|^\.|-$|\.$", hostname):
        logging.fatal("ERROR: Hostname must not begin or end with a minus" " sign or period")
        return False

    return True


"""
pmbootstrap uses this dictionary to save the result of expensive
results, so they work a lot faster the next time they are needed in the
same session. Usually the cache is written to and read from in the same
Python file, with code similar to the following:

def lookup(key):
    if key in pmb.helpers.other.cache["mycache"]:
        return pmb.helpers.other.cache["mycache"][key]
    ret = expensive_operation(args, key)
    pmb.helpers.other.cache["mycache"][key] = ret
    return ret
"""
cache: dict[str, Any] = {
    "apkindex": {},
}
