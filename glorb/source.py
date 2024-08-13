from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class Source(ABC):
    @staticmethod
    @abstractmethod
    def from_dict(v: Dict) -> Source:
        raise NotImplementedError()

    @abstractmethod
    def pull(self, to_path: str, segment: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def has_entry(self, segment: str) -> bool:
        raise NotImplementedError()

    # @abstractmethod
    # def get_modification_time(self, segment: str) -> float:
    #     raise NotImplementedError()

    @abstractmethod
    def compare_modification_time(self, segment: str, local_modification_time: float) -> int:
        raise NotImplementedError()
