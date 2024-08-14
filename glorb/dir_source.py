from __future__ import annotations

import os
import shutil
from typing import Dict, Union

from .updatable_source import UpdatableSource


class DirSource(UpdatableSource):
    def __init__(self, root: str):
        self.root: str = root
        self.data_root: str = os.path.join(root, "data/")
        # self.hashes_path: str = os.path.join(root, "glorbhash")
        # self.hashes: Dict[str, str] = self.read_hashes()
        os.makedirs(self.data_root, exist_ok=True)

    @staticmethod
    def from_dict(v: Dict) -> DirSource:
        return DirSource(v["path"])

    # def read_hashes(self) -> Dict[str, str]:
    #     if not os.path.exists(self.hashes_path):
    #         return {}
    #
    #     hashes = {}
    #
    #     with open(self.hashes_path, "r") as f:
    #         for line in f.readlines():
    #             split_index = line.index(" ")
    #             h = line[:split_index]
    #             uid = line[split_index + 1:-1]
    #             hashes[uid] = h
    #
    #     return hashes
    #
    # def write_hashes(self):
    #     with open(self.hashes_path, "w") as f:
    #         for uid, h in self.hashes.items():
    #             f.write(h + " " + uid + "\n")

    def pull(self, to_path: str, segment: str):
        source_path = self.segment_to_path(segment)
        shutil.copy(source_path, to_path)
        os.utime(to_path, (0, os.path.getmtime(source_path)))

    def push(self, from_path: str, segment: str):
        source_path = self.segment_to_path(segment)

        os.makedirs(os.path.dirname(source_path), exist_ok=True)

        shutil.copy(from_path, source_path)
        os.utime(source_path, (0, os.path.getmtime(from_path)))

        # self.hashes[segment_to_uid(segment)] = hash_file(from_path).hexdigest()
        # self.write_hashes()

    def segment_to_path(self, segment: str) -> str:
        return os.path.join(self.data_root, segment)

    def has_entry(self, segment: str) -> bool:
        return os.path.exists(self.segment_to_path(segment))

    def maybe_has_entry(self, segment: str) -> Union[bool, None]:
        return self.has_entry(segment)

    def remove(self, segment: str):
        os.remove(self.segment_to_path(segment))
        # del self.hashes[segment_to_uid(segment)]
        # self.write_hashes()

    def get_modification_time(self, segment: str) -> float:
        return os.path.getmtime(self.segment_to_path(segment))

    def compare_modification_time(self, segment: str, local_modification_time: float) -> int:
        source_modification_time = self.get_modification_time(segment)

        if source_modification_time > local_modification_time:
            return 1
        elif local_modification_time > source_modification_time:
            return -1

        return 0
