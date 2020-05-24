# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import pmb.config
import pmb.helpers.devices


def sanity_check(info, path):
    # Resolve path for more readable error messages
    path = os.path.realpath(path)

    # Legacy errors
    if "flash_methods" in info:
        raise RuntimeError("deviceinfo_flash_methods has been renamed to"
                           " deviceinfo_flash_method. Please adjust your"
                           " deviceinfo file: " + path)
    if "external_disk" in info or "external_disk_install" in info:
        raise RuntimeError("Instead of deviceinfo_external_disk and"
                           " deviceinfo_external_disk_install, please use the"
                           " new variable deviceinfo_external_storage in your"
                           " deviceinfo file: " + path)
    if "msm_refresher" in info:
        raise RuntimeError("It is enough to specify 'msm-fb-refresher' in the"
                           " depends of your device's package now. Please"
                           " delete the deviceinfo_msm_refresher line in: " +
                           path)
    if "flash_fastboot_vendor_id" in info:
        raise RuntimeError("Fastboot doesn't allow specifying the vendor ID"
                           " anymore (#1830). Try removing the"
                           " 'deviceinfo_flash_fastboot_vendor_id' line in: " +
                           path + " (if you are sure that you need this, then"
                           " we can probably bring it back to fastboot, just"
                           " let us know in the postmarketOS issues!)")
    if "nonfree" in info:
        raise RuntimeError("deviceinfo_nonfree is unused. "
                           "Please delete it in: " + path)
    if "dev_keyboard" in info:
        raise RuntimeError("deviceinfo_dev_keyboard is unused. "
                           "Please delete it in: " + path)
    if "date" in info:
        raise RuntimeError("deviceinfo_date was replaced by deviceinfo_year. "
                           "Set it to the release year in: " + path)

    # "codename" is required
    codename = os.path.basename(os.path.dirname(path))
    if codename.startswith("device-"):
        codename = codename[7:]
    if "codename" not in info or info["codename"] != codename:
        raise RuntimeError("Please add 'deviceinfo_codename=\"" + codename +
                           "\"' to: " + path)

    # "chassis" is required
    chassis_types = pmb.config.deviceinfo_chassis_types
    if "chassis" not in info or not info["chassis"]:
        logging.info("NOTE: the most commonly used chassis types in"
                     " postmarketOS are 'handset' (for phones) and 'tablet'.")
        raise RuntimeError(f"Please add 'deviceinfo_chassis' to: {path}")

    # "chassis" validation
    chassis_type = info["chassis"]
    if chassis_type not in chassis_types:
        raise RuntimeError(f"Unknown chassis type '{chassis_type}', should"
                           f" be one of {', '.join(chassis_types)}. Fix this"
                           f" and try again: {path}")


def deviceinfo(args, device=None):
    """
    :param device: defaults to args.device
    """
    if not device:
        device = args.device

    if not os.path.exists(args.aports):
        logging.fatal("Aports directory is missing, expected: " + args.aports)
        logging.fatal("Please provide a path to the aports directory using the -p flag")
        raise RuntimeError("Aports directory missing")

    path = pmb.helpers.devices.find_path(args, device, 'deviceinfo')
    if not path:
        raise RuntimeError(
            "Device '" + device + "' not found. Run 'pmbootstrap init' to"
            " start a new device port or to choose another device. It may have"
            " been renamed, see <https://postmarketos.org/renamed>")

    ret = {}
    with open(path) as handle:
        for line in handle:
            if not line.startswith("deviceinfo_"):
                continue
            if "=" not in line:
                raise SyntaxError(path + ": No '=' found:\n\t" + line)
            split = line.split("=", 1)
            key = split[0][len("deviceinfo_"):]
            value = split[1].replace("\"", "").replace("\n", "")
            ret[key] = value

    # Assign empty string as default
    for key in pmb.config.deviceinfo_attributes:
        if key not in ret:
            ret[key] = ""

    sanity_check(ret, path)
    return ret
