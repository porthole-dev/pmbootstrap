"""
Copyright 2020 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import os
import re

import pmb.config
import pmb.parse.version

# sh variable name regex: https://stackoverflow.com/a/2821201/3527128

# ${foo}
revar = re.compile(r"\${([a-zA-Z_]+[a-zA-Z0-9_]*)}")

# $foo
revar2 = re.compile(r"\$([a-zA-Z_]+[a-zA-Z0-9_]*)")

# ${var/foo/bar}, ${var/foo/}, ${var/foo} -- replace foo with bar
revar3 = re.compile(r"\${([a-zA-Z_]+[a-zA-Z0-9_]*)/([^/]+)(?:/([^/]*?))?}")

# ${foo#bar} -- cut off bar from foo from start of string
revar4 = re.compile(r"\${([a-zA-Z_]+[a-zA-Z0-9_]*)#(.*)}")


def replace_variable(apkbuild, value: str) -> str:
    # ${foo}
    for match in revar.finditer(value):
        try:
            logging.verbose("{}: replace '{}' with '{}'".format(
                            apkbuild["pkgname"], match.group(0),
                            apkbuild[match.group(1)]))
            value = value.replace(match.group(0), apkbuild[match.group(1)], 1)
        except KeyError:
            logging.debug("{}: key '{}' for replacing '{}' not found, ignoring"
                          "".format(apkbuild["pkgname"], match.group(1),
                                    match.group(0)))

    # $foo
    for match in revar2.finditer(value):
        try:
            newvalue = apkbuild[match.group(1)]
            logging.verbose("{}: replace '{}' with '{}'".format(
                            apkbuild["pkgname"], match.group(0),
                            newvalue))
            value = value.replace(match.group(0), newvalue, 1)
        except KeyError:
            logging.debug("{}: key '{}' for replacing '{}' not found, ignoring"
                          "".format(apkbuild["pkgname"], match.group(1),
                                    match.group(0)))

    # ${var/foo/bar}, ${var/foo/}, ${var/foo}
    for match in revar3.finditer(value):
        try:
            newvalue = apkbuild[match.group(1)]
            search = match.group(2)
            replacement = match.group(3)
            if replacement is None:  # arg 3 is optional
                replacement = ""
            newvalue = newvalue.replace(search, replacement, 1)
            logging.verbose("{}: replace '{}' with '{}'".format(
                            apkbuild["pkgname"], match.group(0), newvalue))
            value = value.replace(match.group(0), newvalue, 1)
        except KeyError:
            logging.debug("{}: key '{}' for replacing '{}' not found, ignoring"
                          "".format(apkbuild["pkgname"], match.group(1),
                                    match.group(0)))

    # ${foo#bar}
    rematch4 = revar4.finditer(value)
    for match in rematch4:
        try:
            newvalue = apkbuild[match.group(1)]
            substr = match.group(2)
            if newvalue.startswith(substr):
                newvalue = newvalue.replace(substr, "", 1)
            logging.verbose("{}: replace '{}' with '{}'".format(
                            apkbuild["pkgname"], match.group(0), newvalue))
            value = value.replace(match.group(0), newvalue, 1)
        except KeyError:
            logging.debug("{}: key '{}' for replacing '{}' not found, ignoring"
                          "".format(apkbuild["pkgname"], match.group(1),
                                    match.group(0)))

    return value


def cut_off_function_names(apkbuild):
    """
    For subpackages: only keep the subpackage name, without the internal
    function name, that tells how to build the subpackage.
    """
    sub = apkbuild["subpackages"]
    for i in range(len(sub)):
        sub[i] = sub[i].split(":", 1)[0]
    apkbuild["subpackages"] = sub
    return apkbuild


def function_body(path, func):
    """
    Get the body of a function in an APKBUILD.

    :param path: full path to the APKBUILD
    :param func: name of function to get the body of.
    :returns: function body in an array of strings.
    """
    func_body = []
    in_func = False
    lines = read_file(path)
    for line in lines:
        if in_func:
            if line.startswith("}"):
                in_func = False
                break
            func_body.append(line)
            continue
        else:
            if line.startswith(func + "() {"):
                in_func = True
                continue
    return func_body


def read_file(path):
    """
    Read an APKBUILD file

    :param path: full path to the APKBUILD
    :returns: contents of an APKBUILD as a list of strings
    """
    with open(path, encoding="utf-8") as handle:
        lines = handle.readlines()
        if handle.newlines != '\n':
            raise RuntimeError("Wrong line endings in APKBUILD: " + path)
    return lines


def parse_attribute(attribute, lines, i, path):
    """
    Parse one attribute from the APKBUILD.

    It may be written across multiple lines, use a quoting sign and/or have
    a comment at the end. Some examples:

    pkgrel=3
    options="!check" # ignore this comment
    arch='all !armhf'
    depends="
        first-pkg
        second-pkg"

    :param attribute: from the APKBUILD, i.e. "pkgname"
    :param lines: \n-terminated list of lines from the APKBUILD
    :param i: index of the line we are currently looking at
    :param path: full path to the APKBUILD (for error message)
    :returns: (found, value, i)
              found: True if the attribute was found in line i, False otherwise
              value: that was parsed from the line
              i: line that was parsed last
    """
    # Check for and cut off "attribute="
    if not lines[i].startswith(attribute + "="):
        return (False, None, i)
    value = lines[i][len(attribute + "="):-1]

    # Determine end quote sign
    end_char = None
    for char in ["'", "\""]:
        if value.startswith(char):
            end_char = char
            value = value[1:]
            break

    # Single line
    if not end_char:
        return (True, value, i)
    if end_char in value:
        value = value.split(end_char, 1)[0]
        return (True, value, i)

    # Parse lines until reaching end quote
    i += 1
    while i < len(lines):
        line = lines[i]
        value += " "
        if end_char in line:
            value += line.split(end_char, 1)[0].strip()
            return (True, value.strip(), i)
        value += line.strip()
        i += 1

    raise RuntimeError("Can't find closing quote sign (" + end_char + ") for"
                       " attribute '" + attribute + "' in: " + path)


def apkbuild(args, path, check_pkgver=True, check_pkgname=True):
    """
    Parse relevant information out of the APKBUILD file. This is not meant
    to be perfect and catch every edge case (for that, a full shell parser
    would be necessary!). Instead, it should just work with the use-cases
    covered by pmbootstrap and not take too long.
    Run 'pmbootstrap apkbuild_parse hello-world' for a full output example.

    :param path: full path to the APKBUILD
    :param check_pkgver: verify that the pkgver is valid.
    :param check_pkgname: the pkgname must match the name of the aport folder
    :returns: relevant variables from the APKBUILD. Arrays get returned as
              arrays.
    """
    # Try to get a cached result first (we assume, that the aports don't change
    # in one pmbootstrap call)
    if path in args.cache["apkbuild"]:
        return args.cache["apkbuild"][path]

    # Read the file and check line endings
    lines = read_file(path)

    # Parse all attributes from the config
    ret = {key: "" for key in pmb.config.apkbuild_attributes.keys()}
    for i in range(len(lines)):
        for attribute, options in pmb.config.apkbuild_attributes.items():
            found, value, i = parse_attribute(attribute, lines, i, path)
            if not found:
                continue

            ret[attribute] = replace_variable(ret, value)

    # Split attributes
    for attribute, options in pmb.config.apkbuild_attributes.items():
        if options.get("array", False):
            # Split up arrays, delete empty strings inside the list
            ret[attribute] = list(filter(None, ret[attribute].split(" ")))

    ret = cut_off_function_names(ret)

    # Sanity check: pkgname
    suffix = "/" + ret["pkgname"] + "/APKBUILD"
    if check_pkgname:
        if not os.path.realpath(path).endswith(suffix):
            logging.info("Folder: '" + os.path.dirname(path) + "'")
            logging.info("Pkgname: '" + ret["pkgname"] + "'")
            raise RuntimeError("The pkgname must be equal to the name of"
                               " the folder, that contains the APKBUILD!")

    # Sanity check: arch
    if not len(ret["arch"]):
        raise RuntimeError("Arch must not be empty: " + path)

    # Sanity check: pkgver
    if check_pkgver:
        if "-r" in ret["pkgver"] or not pmb.parse.version.validate(ret["pkgver"]):
            logging.info("NOTE: Valid pkgvers are described here:")
            logging.info("<https://wiki.alpinelinux.org/wiki/APKBUILD_Reference#pkgver>")
            raise RuntimeError("Invalid pkgver '" + ret["pkgver"] +
                               "' in APKBUILD: " + path)

    # Fill cache
    args.cache["apkbuild"][path] = ret
    return ret


def subpkgdesc(path, function):
    """
    Get the pkgdesc of a subpackage in an APKBUILD.

    :param path: to the APKBUILD file
    :param function: name of the subpackage (e.g. "nonfree_userland")
    :returns: the subpackage's pkgdesc
    """
    # Read all lines
    lines = read_file(path)

    # Prefixes
    prefix_function = function + "() {"
    prefix_pkgdesc = "\tpkgdesc=\""

    # Find the pkgdesc
    in_function = False
    for line in lines:
        if in_function:
            if line.startswith(prefix_pkgdesc):
                return line[len(prefix_pkgdesc):-2]
        elif line.startswith(prefix_function):
            in_function = True

    # Failure
    if not in_function:
        raise RuntimeError("Could not find subpackage function, no line starts"
                           " with '" + prefix_function + "' in " + path)
    raise RuntimeError("Could not find pkgdesc of subpackage function '" +
                       function + "' (spaces used instead of tabs?) in " +
                       path)


def kernels(args, device):
    """
    Get the possible kernels from a device-* APKBUILD.

    :param device: the device name, e.g. "lg-mako"
    :returns: None when the kernel is hardcoded in depends
    :returns: kernel types and their description (as read from the subpackages)
              possible types: "downstream", "stable", "mainline"
              example: {"mainline": "Mainline description",
                        "downstream": "Downstream description"}
    """
    # Read the APKBUILD
    apkbuild_path = args.aports + "/device/device-" + device + "/APKBUILD"
    if not os.path.exists(apkbuild_path):
        return None
    subpackages = apkbuild(args, apkbuild_path)["subpackages"]

    # Read kernels from subpackages
    ret = {}
    subpackage_prefix = "device-" + device + "-kernel-"
    for subpackage in subpackages:
        if not subpackage.startswith(subpackage_prefix):
            continue
        name = subpackage[len(subpackage_prefix):]
        # FIXME: We should use the specified function name here,
        # but it's removed in cut_off_function_names()
        func = "kernel_" + name.replace('-', '_')
        desc = pmb.parse._apkbuild.subpkgdesc(apkbuild_path, func)
        ret[name] = desc

    # Return
    if ret:
        return ret
    return None
