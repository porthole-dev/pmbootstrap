# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path, PosixPath
from typing import Any, Dict
from pmb.helpers import logging
import configparser
import os
import sys
import pmb.config
from pmb.types import Config
from pmb.types import PmbArgs


def sanity_check(args: PmbArgs, cfg: Config, key, allowed, print_path):
    value = getattr(cfg, key)

    if value in allowed:
        return

    logging.error(f"pmbootstrap.cfg: invalid value for {key}: '{value}'")
    logging.error(f"Allowed: {', '.join(allowed)}")

    if print_path:
        logging.error(f"Fix it here and try again: {args.config}")

    sys.exit(1)


def sanity_checks(args: PmbArgs, cfg: Config, print_path=True):
    for key, allowed in pmb.config.allowed_values.items():
        sanity_check(args, cfg, key, allowed, print_path)


def load(args: PmbArgs) -> Config:
    config = Config()

    cfg = configparser.ConfigParser()
    if os.path.isfile(args.config):
        cfg.read(args.config)

    if "pmbootstrap" not in cfg:
        cfg["pmbootstrap"] = {}
    if "providers" not in cfg:
        cfg["providers"] = {}

    for key in Config.__dict__.keys():
        if key == "providers":
            setattr(config, key, cfg["providers"])
        # Handle whacky type conversions
        elif key == "mirrors_postmarketos":
            config.mirrors_postmarketos = cfg["pmbootstrap"]["mirrors_postmarketos"].split(",")
        # Convert strings to paths
        elif type(getattr(Config, key)) == PosixPath:
            setattr(config, key, Path(cfg["pmbootstrap"][key]))
        elif isinstance(getattr(Config, key), bool):
            setattr(config, key, cfg["pmbootstrap"][key].lower() == "true")
        elif key in cfg["pmbootstrap"]:
            setattr(config, key, cfg["pmbootstrap"][key])

    sanity_checks(args, config)

    return config

def save(output: Path, config: Config):
    logging.debug(f"Save config: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch(0o700, exist_ok=True)
    
    cfg = configparser.ConfigParser()
    cfg["pmbootstrap"] = {}
    cfg["providers"] = {}

    for key in Config.__dict__.keys():
        print(key)
        if key == "providers":
            cfg["providers"] = config.providers
        # Handle whacky type conversions
        elif key == "mirrors_postmarketos":
            cfg["pmbootstrap"]["mirrors_postmarketos"] = ",".join(config.mirrors_postmarketos)
        # Convert strings to paths
        elif type(getattr(Config, key)) == Path:
            cfg["pmbootstrap"][key] = str(getattr(config, key))
        elif isinstance(getattr(Config, key), bool):
            cfg["pmbootstrap"][key] = str(getattr(config, key))
        else:
            cfg["pmbootstrap"] = getattr(config, key)

    with output.open("w") as handle:
        cfg.write(handle)
