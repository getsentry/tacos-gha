#!/usr/bin/env py.test
from __future__ import annotations

import contextlib
from os import environ

from lib import json as JSON
from lib.types import Environ
from lib.types import Generator
from lib.types import OSPath

from .core import run
from .io import banner as banner
from .io import info as info
from .io import xtrace
from .json import json

# TODO: centralize reused type aliases
Command = tuple[object, ...]


@contextlib.contextmanager
def cd(
    dirname: OSPath, env: Environ = environ, *, direnv: bool = True
) -> Generator[OSPath]:
    oldpwd = OSPath(env["PWD"])

    # double-check that $PWD stays accurate:
    assert oldpwd.samefile(OSPath.cwd()), (oldpwd, OSPath.cwd())

    newpwd = oldpwd / dirname
    if newpwd.samefile(oldpwd):  # we're already there
        yield oldpwd
        return

    env["PWD"] = str(newpwd)
    xtrace(("cd", dirname))
    with contextlib.chdir(dirname):
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
        yield dirname

        # show the un-cd, and reflect it in $PWD
        env["PWD"] = str(oldpwd)
        xtrace(("cd", oldpwd))
