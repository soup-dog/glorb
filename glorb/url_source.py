from typing import Dict, Union
import requests
import shutil

from .source import Source


# from https://stackoverflow.com/a/39217788
def download_file(url: str, filename: str) -> None:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)


class URLSource(Source):
    def __init__(self, base: str):
        self.base: str = base

    @staticmethod
    def from_dict(v: Dict) -> Source:
        return URLSource(v["base_url"])

    def pull(self, to_path: str, segment: str) -> None:
        download_file(self.base + segment, to_path)

    def compare_modification_time(self, segment: str, local_modification_time: float) -> int:
        return 1

    def maybe_has_entry(self, segment: str) -> Union[bool, None]:
        return None

    def has_entry(self, segment: str) -> bool:
        raise NotImplementedError()
