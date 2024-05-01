#!/usr/bin/env py.test

# TODO: Delete env.sh

from __future__ import annotations

from os import environ

from lib import json
from lib.sh import sh
from lib.types import Environ
from lib.types import OSPath
from lib.types import Path


def get_current_host(env: Environ) -> str:
    for var in ("HOST", "HOSTNAME"):
        if var in env:
            return env[var]
    else:
        import socket

        return socket.gethostname()


def get_current_user(env: Environ) -> str:
    for var in ("USER", "LOGNAME"):
        if var in env:
            return env[var]
    else:
        import getpass

        return getpass.getuser()


here = sh.get_HERE(__file__)
LIB = here
USER = environ["USER"] = get_current_user(environ)
HOST = environ["HOST"] = get_current_host(environ)
HOSTNAME = environ["HOSTNAME"] = environ["HOST"]

TF_LOCK_ENONE = 2
TF_LOCK_EHELD = 3

TACOS_GHA_HOME = Path(
    environ.setdefault("TACOS_GHA_HOME", str(here / "../../.."))
)


def path_prepend(env_name: str, env_val: object) -> None:
    r"""Preprend to a colon delimited environment variable.

    >>> path_prepend('name', 'val')
    >>> path_prepend('name', Path('val2'))
    >>> environ['name']
    'val2:val'
    """
    pythonpath = environ.get(env_name, "")
    if pythonpath:
        pythonpath_list = pythonpath.split(":")
    else:
        pythonpath_list = []
    pythonpath_list.insert(0, str(env_val))
    environ[env_name] = ":".join(pythonpath_list)


path_prepend("PYTHONPATH", TACOS_GHA_HOME)
path_prepend("PATH", TACOS_GHA_HOME / "/bin")
path_prepend("PATH", here / "bin")


def tf_working_dir(root_module: OSPath) -> OSPath:
    if (root_module / "terragrunt.hcl").exists():
        with sh.cd(root_module):
            # validate-inputs makes terragrunt generate its templates
            sh.run(
                (
                    "terragrunt",
                    "--terragrunt-no-auto-init=false",
                    "validate-inputs",
                )
            )
            terragrunt_info = sh.json(
                (
                    "terragrunt",
                    "--terragrunt-no-auto-init=false",
                    "terragrunt-info",
                )
            )
            terragrunt_info = json.assert_dict_of_strings(terragrunt_info)
            return OSPath(terragrunt_info["WorkingDir"])

    else:
        return root_module
