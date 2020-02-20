# Copyright 2020 Attila Szollosi
# SPDX-License-Identifier: GPL-3.0-or-later
import glob
import logging
import re
import os

import pmb.build
import pmb.config
import pmb.parse
import pmb.helpers.pmaports


def is_set(config, option):
    """
    Check, whether a boolean or tristate option is enabled
    either as builtin or module.
    """
    return re.search("^CONFIG_" + option + "=[ym]", config, re.M) is not None


def check_config(config_path, config_path_pretty, config_arch, pkgver, details=False):
    logging.debug("Check kconfig: " + config_path)
    with open(config_path) as handle:
        config = handle.read()

    # Loop through necessary config options, and print a warning,
    # if any is missing
    ret = True
    for rule, archs_options in pmb.config.necessary_kconfig_options.items():
        # Skip options irrelevant for the current kernel's version
        if not pmb.parse.version.check_string(pkgver, rule):
            continue

        for archs, options in archs_options.items():
            if archs != "all":
                # Split and check if the device's architecture architecture has special config
                # options. If option does not contain the architecture of the device
                # kernel, then just skip the option.
                architectures = archs.split(" ")
                if config_arch not in architectures:
                    continue

            for option, option_value in options.items():
                if option_value not in [True, False]:
                    raise RuntimeError("kconfig check code can only handle"
                                       " True/False right now, given value '" +
                                       str(option_value) + "' is not supported. If you"
                                       " need this, please open an issue.")
                if option_value != is_set(config, option):
                    ret = False
                    if details:
                        should = "should" if option_value else "should *not*"
                        link = ("https://wiki.postmarketos.org/wiki/"
                                "Kernel_configuration#CONFIG_" + option)
                        logging.info("WARNING: " + config_path_pretty + ": CONFIG_" + option + " " +
                                     should + " be set. See <" + link +
                                     "> for details.")
                    else:
                        logging.warning("WARNING: " + config_path_pretty + " isn't configured"
                                        " properly for postmarketOS, run"
                                        " 'pmbootstrap kconfig check' for"
                                        " details!")
                        break
    return ret


def check(args, pkgname, details=False):
    """
    Check for necessary kernel config options.

    :returns: True when the check was successful, False otherwise
    """
    # Pkgname: allow omitting "linux-" prefix
    if pkgname.startswith("linux-"):
        flavor = pkgname.split("linux-")[1]
        logging.info("PROTIP: You can simply do 'pmbootstrap kconfig check " +
                     flavor + "'")
    else:
        flavor = pkgname

    # Read all kernel configs in the aport
    ret = True
    aport = pmb.helpers.pmaports.find(args, "linux-" + flavor)
    pkgver = pmb.parse.apkbuild(args, aport + "/APKBUILD")["pkgver"]
    for config_path in glob.glob(aport + "/config-*"):
        # The architecture of the config is in the name, so it just needs to be
        # extracted
        config_arch = os.path.basename(config_path).split(".")[1]
        config_path_pretty = "linux-" + flavor + "/" + os.path.basename(config_path)
        ret &= check_config(config_path, config_path_pretty, config_arch, pkgver, details)
    return ret


def extract_arch(config_file):
    # Extract the architecture out of the config
    with open(config_file) as f:
        config = f.read()
    if is_set(config, "ARM"):
        return "armv7"
    elif is_set(config, "ARM64"):
        return "aarch64"
    elif is_set(config, "X86_32"):
        return "x86"
    elif is_set(config, "X86_64"):
        return "x86_64"

    # No match
    logging.info("WARNING: failed to extract arch from kernel config")
    return "unknown"


def extract_version(config_file):
    # Try to extract the version string out of the comment header
    with open(config_file) as f:
        # Read the first 3 lines of the file and get the third line only
        text = [next(f) for x in range(3)][2]
    ver_match = re.match(r"# Linux/\S+ (\S+) Kernel Configuration", text)
    if ver_match:
        return ver_match.group(1)

    # No match
    logging.info("WARNING: failed to extract version from kernel config")
    return "unknown"


def check_file(args, config_file, details=False):
    arch = extract_arch(config_file)
    version = extract_version(config_file)
    logging.debug("Check kconfig: parsed arch=" + arch + ", version=" +
                  version + " from file: " + config_file)
    return check_config(config_file, config_file, arch, version, details)
