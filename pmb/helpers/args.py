# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.config
from pmb.core.context import Context
from pmb.core.pkgrepo import pkgrepo_default_path
from pmb.types import PmbArgs
import pmb.helpers.git
import pmb.helpers.args

__args: PmbArgs = PmbArgs()

"""This file constructs the args variable, which is passed to almost all
   functions in the pmbootstrap code base. Here's a listing of the kind of
   information it stores.

    1. Argparse
       Variables directly from command line argument parsing (see
       pmb/parse/arguments.py, the "dest" parameter of the add_argument()
       calls defines where it is stored in args).

       Examples:
       args.action ("zap", "chroot", "build" etc.)
       args.as_root (True when --as-root is passed)
       ...

    2. Argparse merged with others
       Variables from the user's config file (~/.config/pmbootstrap.cfg) that
       can be overridden from the command line (pmb/parse/arguments.py) and
       fall back to the defaults defined in pmb/config/__init__.py (see
       "defaults = {..."). The user's config file gets generated interactively
        with "pmbootstrap init".

       Examples:
       args.aports ("$WORK/cache_git/pmaports", override with --aports)
       args.device ("samsung-i9100", "qemu-amd64" etc.)
       get_context().config.work ("/home/user/.local/var/pmbootstrap", override with --work)

    3. Parsed configs
       Similar to the cache above, specific config files get parsed and added
       to args, so they can get accessed quickly (without parsing the configs
       over and over). These configs are not only used in one specific
       location, so having a short name for them increases readability of the
       code as well.

       Examples:
       deviceinfo (e.g. {"name": "Mydevice", "arch": "armhf", ...})
"""


def init(args: PmbArgs) -> PmbArgs:
    global __args
    # Basic initialization
    # print(json.dumps(args.__dict__))
    # sys.exit(0)
    config = pmb.config.load(args.config)

    if args.aports and not args.aports.exists():
        raise ValueError(
            "pmaports path (specified with --aports) does" f" not exist: {args.aports}"
        )

    # Override config at runtime with command line arguments
    for key, _ in vars(config).items():
        if key.startswith("_") or key == "user":
            continue
        value = getattr(args, key, None)
        if value:
            print(f"Overriding config.{key} with {value}")
            setattr(config, key, value)

        # Deny accessing the attribute via args
        if hasattr(args, key):
            delattr(args, key)

    # Handle --mirror-alpine and --mirror-pmos
    value = getattr(args, "mirror_alpine", None)
    if value:
        config.mirrors["alpine"] = value
    value = getattr(args, "mirror_postmarketos", None)
    if value:
        config.mirrors["pmaports"] = value

    # Configure runtime context
    context = Context(config)
    context.command_timeout = args.timeout
    context.details_to_stdout = args.details_to_stdout
    context.quiet = args.quiet
    context.offline = args.offline
    context.command = args.action
    context.cross = args.cross
    context.assume_yes = getattr(args, "assume_yes", False)
    context.force = getattr(args, "force", False)

    # Initialize context
    pmb.core.context.set_context(context)

    # Initialize logs (we could raise errors below)
    pmb.helpers.logging.init(context.log, args.verbose, context.details_to_stdout)

    # Initialization code which may raise errors
    if args.action not in [
        "init",
        "checksum",
        "config",
        "bootimg_analyze",
        "log",
        "pull",
        "shutdown",
        "zap",
    ]:
        pmb.config.pmaports.read_config()
        pmb.helpers.git.parse_channels_cfg(pkgrepo_default_path())

    # Remove attributes from args so they don't get used by mistake
    delattr(args, "timeout")
    delattr(args, "details_to_stdout")
    delattr(args, "log")
    delattr(args, "quiet")
    delattr(args, "offline")
    if hasattr(args, "force"):
        delattr(args, "force")
    if hasattr(args, "device"):
        delattr(args, "device")

    # Copy all properties from args to out that don't start with underscores
    for key, value in vars(args).items():
        if not key.startswith("_") and not key == "from_argparse":
            setattr(__args, key, value)

    # print(json.dumps(__args.__dict__))

    # sys.exit(0)

    return __args


# def update_work(args: PmbArgs, work):
#     """Update the work path in args.work and wherever $WORK was used."""
#     # Start with the unmodified args from argparse
#     args_new = copy.deepcopy(args.from_argparse)

#     # Keep from the modified args:
#     # * the unmodified args from argparse (to check if --aports was specified)
#     args_new.from_argparse = args.from_argparse

#     # Generate modified args again, replacing $WORK with the new work folder
#     # When args.log is different, this also opens the log in the new location
#     args_new.work = work
#     args_new = pmb.helpers.args.init(args_new)

#     # Overwrite old attributes of args with the new attributes
#     for key in vars(args_new):
#         setattr(args, key, getattr(args_new, key))


def please_i_really_need_args() -> PmbArgs:
    import traceback

    traceback.print_stack()
    print("FIXME: retrieved args where it shouldn't be needed!")
    return __args
