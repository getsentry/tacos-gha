#!/usr/bin/env py.test
from __future__ import annotations

import contextlib
from os import environ
from pathlib import Path

from lib import json as JSON
from lib.types import Environ
from lib.types import Generator

from .core import run
from .io import banner as banner
from .io import info as info
from .io import quiet as quiet
from .io import xtrace
from .json import json

# TODO: centralize reused type aliases
Command = tuple[object, ...]


@contextlib.contextmanager
def cd(
    dirname: Path, direnv: bool = True, env: Environ = environ
) -> Generator[Path]:
    xtrace(("cd", dirname))
    with contextlib.chdir(dirname):
        env["PWD"] = str(Path(env["PWD"]) / dirname)
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
        yield dirname
