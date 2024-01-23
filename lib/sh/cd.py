#!/usr/bin/env py.test
from __future__ import annotations

from contextlib import contextmanager
from os import chdir
from os import environ

from lib import json as JSON
from lib.types import Environ
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path

from .core import run
from .io import banner as banner
from .io import info as info
from .io import xtrace
from .json import json

# TODO: centralize reused type aliases
Command = tuple[object, ...]


@contextmanager
def cd(
    dirname: Path, env: Environ = environ, *, direnv: bool = True
) -> Generator[Path]:
    oldpwd = Path.cwd(env)

    newpwd = oldpwd / dirname
    cwd = OSPath.cwd()
    if newpwd == oldpwd and cwd.samefile(newpwd):  # we're already there
        yield oldpwd
        return

    xtrace(("cd", dirname))
    env["PWD"] = str(newpwd)
    chdir(dirname)
    if direnv:
        run(("direnv", "allow"))
        direnv_json: JSON.Value = json(("direnv", "export", "json"))
        if direnv_json is None:
            pass  # nothing to do
        elif isinstance(direnv_json, dict):
            for key, value in direnv_json.items():
                if value is None:
                    env.pop(key, None)
                else:
                    assert isinstance(value, str), value
                    env[key] = value
        else:
            raise AssertionError(f"expected dict, got {type(direnv_json)}")
    try:
        yield newpwd
    finally:  # undo the cd and log it
        chdir(oldpwd)
        env["PWD"] = str(oldpwd)
        xtrace(("popd",))
        info(oldpwd, "<-", newpwd)
