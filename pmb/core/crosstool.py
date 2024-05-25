# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import Namespace
import enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from pmb.core.chroot import ChrootType
from pmb.types import PathString

class CrossToolTarget(enum.Enum):
    BUILDROOT = 0
    ROOTFS = 1

class CrossTool():
    __target: CrossToolTarget
    __package: str
    __paths: List[Path]

    def __init__(self, target: CrossToolTarget, package: str, paths: List[PathString]):
        self.__target = target
        self.__package = package
        self.__paths = list(map(lambda p: Path(p) if isinstance(p, str) else p, paths))

    def __repr__(self) -> str:
        return f"CrossTool({self.__target}, {self.__package}, {self.__paths})"

    @property
    def package(self) -> str:
        return self.__package

    @property
    def paths(self) -> List[Path]:
        return self.__paths

    def should_install(self, target: ChrootType) -> bool:
        if target == ChrootType.BUILDROOT and self.__target == CrossToolTarget.BUILDROOT:
            return True
        if target == ChrootType.ROOTFS or target == ChrootType.INSTALLER and self.__target == CrossToolTarget.ROOTFS:
            return True
        
        return False
