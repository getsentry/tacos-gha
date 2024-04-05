#!/usr/bin/env py.test

# TODO: Delete env.sh

from __future__ import annotations

from os import environ

from lib.sh import sh
from lib.types import OSPath
from lib.types import Path

from ..release import get_current_host
from ..release import get_current_user

HERE = sh.get_HERE(__file__)
USER = environ["USER"] = get_current_user(environ)
HOST = environ["HOST"] = get_current_host(environ)
HOSTNAME = environ["HOSTNAME"] = environ["HOST"]

TF_LOCK_ENONE = 2
TF_LOCK_EHELD = 3


TACOS_GHA_HOME = environ.setdefault("TACOS_GHA_HOME", str(HERE / "../../.."))


def path_prepend(env_name: str, env_val: str) -> None:
    r"""Preprend to a colon delimited environment variable.

    >>> path_prepend('name', 'val')
    >>> path_prepend('name', 'val2')
    >>> environ['name']
    'val2:val'
    """
    pythonpath = environ.get(env_name, "")
    if pythonpath:
        pythonpath_list = pythonpath.split(":")
    else:
        pythonpath_list = []
    pythonpath_list.insert(0, env_val)
    environ[env_name] = ":".join(pythonpath_list)


path_prepend("PYTHONPATH", TACOS_GHA_HOME)
path_prepend("PATH", TACOS_GHA_HOME + "/bin")
path_prepend("PATH", TACOS_GHA_HOME + "/lib/tf_lock/bin")


def tf_working_dir(root_module: OSPath) -> Path:
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
            assert isinstance(terragrunt_info, dict), terragrunt_info
            working_dir = terragrunt_info.get("WorkingDir")
            assert isinstance(working_dir, str)
            return Path(working_dir)

    else:
        return root_module
