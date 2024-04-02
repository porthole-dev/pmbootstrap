# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import glob

import pmb.config.pmaports
import pmb.helpers.repo


progress_done = 0
progress_total = 0
progress_step = None


def get_arch(args):
    if args.arch:
        return args.arch

    if args.build_default_device_arch:
        return args.deviceinfo["arch"]

    return pmb.config.arch_native


def check_repo_arg(args):
    cfg = pmb.config.pmaports.read_config_repos(args)
    repo = args.repository

    if repo in cfg:
        return

    if not cfg:
        raise ValueError("pmaports.cfg of current branch does not have any"
                         " sections starting with 'repo:'")

    logging.info(f"Valid repositories: {', '.join(cfg.keys())}")
    raise ValueError(f"Couldn't find section 'repo:{repo}' in pmaports.cfg of"
                     " current branch")


def check_existing_pkgs(args, arch):
    channel = pmb.config.pmaports.read_config(args)["channel"]
    path = f"{args.work}/packages/{channel}/{arch}"

    if glob.glob(f"{path}/*"):
        logging.info(f"Packages path: {path}")

        msg = f"Found previously built packages for {channel}/{arch}, run" \
              " 'pmbootstrap zap -p' first"
        if pmb.parse.arch.cpu_emulation_required(arch):
            msg += " or remove the path manually (to keep cross compilers if" \
                   " you just built them)"

        raise RuntimeError(f"{msg}!")


def get_steps(args):
    cfg = pmb.config.pmaports.read_config_repos(args)
    prev_step = 0
    ret = {}

    for key, packages in cfg[args.repository].items():
        if not key.startswith("bootstrap_"):
            continue

        step = int(key.split("bootstrap_", 1)[1])
        assert step == prev_step + 1, (f"{key}: wrong order of steps, expected"
            f" bootstrap_{prev_step + 1} (previous: bootstrap_{prev_step})")
        prev_step = step

        ret[key] = packages

    return ret


def get_suffix(args, arch):
    if pmb.parse.arch.cpu_emulation_required(arch):
        return f"buildroot_{arch}"
    return "native"


def get_packages(bootstrap_line):
    ret = []
    for word in bootstrap_line.split(" "):
        if word.startswith("["):
            continue
        ret += [word]
    return ret


def set_progress_total(args, steps, arch):
    global progress_total

    progress_total = 0

    # Add one progress point per package
    for step, bootstrap_line in steps.items():
        progress_total += len(get_packages(bootstrap_line))

    # Add progress points per bootstrap step
    progress_total += len(steps) * 2

    # Foreign arch: need to initialize one additional chroot each step
    if pmb.parse.arch.cpu_emulation_required(arch):
        progress_total += len(steps)


def log_progress(msg):
    global progress_done

    percent = int(100 * progress_done / progress_total)
    logging.info(f"*** {percent}% [{progress_step}] {msg} ***")

    progress_done += 1


def run_steps(args, steps, arch, suffix):
    global progress_step

    for step, bootstrap_line in steps.items():
        progress_step = step.replace("bootstrap_", "BOOTSTRAP=")

        log_progress("zapping")
        pmb.chroot.zap(args, confirm=False)

        usr_merge = pmb.chroot.UsrMerge.OFF
        if "[usr_merge]" in bootstrap_line:
            usr_merge = pmb.chroot.UsrMerge.ON

        if suffix != "native":
            log_progress(f"initializing native chroot (merge /usr: {usr_merge.name})")
            # Native chroot needs pmOS binary package repo for cross compilers
            pmb.chroot.init(args, "native", usr_merge)

        log_progress(f"initializing {suffix} chroot (merge /usr: {usr_merge.name})")
        # Initialize without pmOS binary package repo
        pmb.chroot.init(args, suffix, usr_merge, postmarketos_mirror=False)

        for package in get_packages(bootstrap_line):
            log_progress(f"building {package}")
            bootstrap_stage = int(step.split("bootstrap_", 1)[1])
            pmb.build.package(args, package, arch, force=True,
                              strict=True, bootstrap_stage=bootstrap_stage)

    log_progress("bootstrap complete!")


def main(args):
    check_repo_arg(args)

    arch = get_arch(args)
    check_existing_pkgs(args, arch)

    steps = get_steps(args)
    suffix = get_suffix(args, arch)

    set_progress_total(args, steps, arch)
    run_steps(args, steps, arch, suffix)


def require_bootstrap_error(repo, arch, trigger_str):
    """
    Tell the user that they need to do repo_bootstrap, with some context.

    :param repo: which repository
    :param arch: for which architecture
    :param trigger_str: message for the user to understand what caused this
    """
    logging.info(f"ERROR: Trying to {trigger_str} with {repo} enabled, but the"
                 f" {repo} repo needs to be bootstrapped first.")
    raise RuntimeError(f"Run 'pmbootstrap repo_bootstrap {repo} --arch={arch}'"
                       " and then try again.")


def require_bootstrap(args, arch, trigger_str):
    """
    Check if repo_bootstrap was done, if any is needed.

    :param arch: for which architecture
    :param trigger_str: message for the user to understand what caused this
    """
    if pmb.config.other.is_systemd_selected(args):
        pmb.helpers.repo.update(args, arch)
        pkg = pmb.parse.apkindex.package(args, "postmarketos-base-systemd",
                                         arch, False)
        if not pkg:
            require_bootstrap_error("systemd", arch, trigger_str)
