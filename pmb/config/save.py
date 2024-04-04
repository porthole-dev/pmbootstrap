# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pmb.helpers import logging

from pmb.core.types import PmbArgs


def save(args: PmbArgs, cfg):
    logging.debug(f"Save config: {args.config}")
    os.makedirs(os.path.dirname(args.config), 0o700, True)
    with open(args.config, "w") as handle:
        cfg.write(handle)
