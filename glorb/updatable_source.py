from abc import ABC, abstractmethod

from .source import Source


class UpdatableSource(Source, ABC):
    @abstractmethod
    def push(self, from_path: str, segment: str):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, segment: str) -> None:
        raise NotImplementedError()
