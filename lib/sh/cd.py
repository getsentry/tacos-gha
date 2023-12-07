#!/usr/bin/env py.test
from __future__ import annotations

from os import environ
from typing import MutableMapping

from lib import json as JSON

from .core import run
from .io import banner as banner
from .io import info as info
from .io import quiet as quiet
from .io import xtrace
from .json import json

# TODO: centralize reused type aliases
Command = tuple[object, ...]


def cd(
    dirname: str, direnv: bool = True, env: MutableMapping[str, str] = environ
) -> None:
    from os import chdir

    xtrace(("cd", dirname))
    chdir(dirname)
    # TODO: set env[PWD] to absolute path
    if direnv:
        run(("direnv", "allow"))
        direnv_json: JSON.Value = json(("direnv", "export", "json"))
        if not isinstance(direnv_json, dict):
            raise AssertionError(f"expected dict, got {type(direnv_json)}")
        for key, value in direnv_json.items():
            if value is None:
                env.pop(key, None)
            else:
                assert isinstance(value, str), value
                env[key] = value
