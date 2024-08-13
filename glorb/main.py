from __future__ import annotations

import click
import yaml
import os
import hashlib
from typing import *

from .source import Source
from .updatable_source import UpdatableSource
from .dir_source import DirSource


if not os.path.isfile("glorb.yaml"):
    print(f"Could not find glorb.yaml in {os.getcwd()}.")
    exit(1)

with open("glorb.yaml", "rb") as f:
    config = yaml.safe_load(f.read())


has_git = os.path.isdir(".git")


GITIGNORE_MESSAGE = \
    """# +---------------------------------------------------------------------------------+
# | This file is AUTOGENERATED. ANY CHANGES made to this file will NOT BE RETAINED. |
# +---------------------------------------------------------------------------------+"""


def write_gitignore(segments: List[str]):
    with open("glorb.gitignore", "w") as f:
        f.write(GITIGNORE_MESSAGE + "\n\n")

        for segment in segments:
            f.write(segment + "\n")

        f.write("\n")

        f.write(GITIGNORE_MESSAGE)


def read_glorbfile():
    uid_source_map = {}

    try:
        with open("glorbfile.yaml", "rb") as f:
            data = yaml.safe_load(f.read())

            if data is None:
                return {}

            for entry in data:
                uid_source_map[entry["uid"]] = entry["source"]
    except FileNotFoundError:
        return {}

    return uid_source_map


def write_glorbfile(uid_source_map: Dict[str, str]):
    with open("glorbfile.yaml", "w") as f:
        data = [{"uid": uid, "source": source} for uid, source in uid_source_map.items()]

        yaml.safe_dump(data, f)


uid_source_map = read_glorbfile()


def hash_file(path: str, chunk_size: int = 8192):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)

    return h


# class ZipSource(Source):
#     DATA_ROOT = "data/"
#
#     def __init__(self, path: str):
#         self.zipfile = zipfile.ZipFile(path, "a")
#
#     # def fetch(self, relative_path: str, to_path: str):
#         # self.zipfile.extract(from_path, os.path.join(ZipSource.DATA_ROOT, relative_path))
#
#     def push(self, from_path: str, relative_path: str):
#         self.zipfile.write(from_path, os.path.join(ZipSource.DATA_ROOT, relative_path))


def segment_to_uid(segment: str) -> str:
    return os.path.normpath(segment)


@click.group()
def cli():
    pass


def try_get(d: Dict, key: str, message: str = "", exit_code: int = 1) -> Any:
    try:
        return d[key]
    except KeyError:
        print(message)
        exit(exit_code)


def try_get_default(d: Dict, key: Dict, default: Any) -> Any:
    try:
        return d[key]
    except KeyError:
        return default


def prompt_confirm(message: str = "Are you sure you want to do that? (y/n)\n"):
    while True:
        response = input(message)
        if response == "y" or response == "Y":
            return
        if response == "n" or response == "N":
            print("Aborted.")
            exit(1)


def get_source(source_name: str) -> Source:
    sources = try_get(config, "sources", "Missing entry \"sources\".")
    source_dict = try_get(sources, source_name, f"No source with name {source_name}")
    type_ = try_get({"dir": DirSource}, source_dict["type"],
                    f"Unrecognised source type {source_dict['type']}.")

    return type_.from_dict(source_dict)


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.argument("source_name")
# @click.option("--segment-override", type=str)
def add(path, source_name):
    source = get_source(source_name)

    segment = os.path.relpath(path, os.getcwd())
    uid = segment_to_uid(segment)

    if uid in uid_source_map.keys():
        print(f"File {path} already tracked in source {uid_source_map[uid]}.")
        exit(1)

    if isinstance(source, UpdatableSource):
        source.push(path, segment)

    uid_source_map[segment] = source_name

    write_glorbfile(uid_source_map)

    if has_git:
        write_gitignore(list(uid_source_map.keys()))


@cli.command()
@click.argument("path", type=click.Path())
def untrack(path: str):
    segment = os.path.relpath(path, os.getcwd())
    uid = segment_to_uid(segment)

    source_name = try_get(uid_source_map, uid, f"File {path} not tracked.")
    source = get_source(source_name)

    if isinstance(source, UpdatableSource):
        source.remove(segment)

    del uid_source_map[segment]

    write_glorbfile(uid_source_map)

    if has_git:
        write_gitignore(list(uid_source_map.keys()))


@cli.command()
@click.argument("path", type=click.Path(dir_okay=False))
@click.option("--force/--no-force", type=bool, default=False)
def pull(path, force):
    segment = os.path.relpath(path, os.getcwd())
    uid = segment_to_uid(segment)

    source_name = try_get(uid_source_map, uid, f"File {path} not tracked.")
    source = get_source(source_name)

    if (os.path.exists(path)
            and source.compare_modification_time(segment, os.path.getmtime(path)) == -1
            and not force):
        prompt_confirm("The file to pull to has a later modification date than the source file. Are you sure you want to overwrite it? (y/n)\n")

    source.pull(path, segment)


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--force/--no-force", type=bool, default=False)
def push(path, force):
    segment = os.path.relpath(path, os.getcwd())
    uid = segment_to_uid(segment)

    source_name = try_get(uid_source_map, uid, f"File {path} not tracked.")
    source = get_source(source_name)

    if not isinstance(source, UpdatableSource):
        print(f"File {path} is stored in source type {config['sources'][source_name]['type']}, which does not support pushing.")
        exit(1)

    if source.compare_modification_time(segment, os.path.getmtime(path)) == 1 and not force:
        prompt_confirm("The source file has a later modification date than the file to push. Are you sure you want to overwrite it? (y/n)\n")

    source.push(path, segment)


@cli.command
def sync():
    for uid, source_name in uid_source_map.items():
        path = os.path.join(os.getcwd(), uid)
        source = get_source(source_name)

        comparison = source.compare_modification_time(uid, os.path.getmtime(path))

        if comparison == 1:  # source newer
            source.pull(path, uid)
            print(f"PULLED \"{uid}\"")
        elif comparison == -1 and isinstance(source, UpdatableSource):  # local newer
            source.push(path, uid)
            print(f"PUSHED \"{uid}\"")


if __name__ == '__main__':
    cli()
