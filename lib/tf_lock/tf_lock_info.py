#!/usr/bin/env python3
"""Print the metadata of the terraform state lock.

No arguments: like terraform/terragrunt this operates on $PWD.


$ sudo-gcp tf-lock-info | jq .
{
  "ID": "1710368348617077",
  "Path": "gs://sac-dev-tf--team-sre/regions/multi-tenant/tacos-gha/de/terraform.tfstate/default.tflock",
  "Operation": "OperationTypeInvalid",
  "Who": "bukzor@9685.ops.getsentry.github.invalid",
  "Version": "1.5.3",
  "Created": "2024-03-13 22:19:08.45158468 +0000 UTC",
  "Info": "",
  "lock": true
}
"""

from __future__ import annotations

from lib import json
from lib.functions import config_lines
from lib.functions import one
from lib.sh import sh
from lib.types import ExitCode
from lib.types import OSPath
from lib.types import Path
from lib.user_error import UserError

from .lib.env import LIB

CACHE_PATH = Path(".config/tf-lock-info/Path")


def cache_get(tg_root_module: OSPath) -> str | None:
    if (tg_root_module / CACHE_PATH).exists():
        with (tg_root_module / CACHE_PATH).open() as cache:
            return one(config_lines(cache))
    return None


def cache_put(tg_root_module: OSPath, path: str) -> None:
    cache = tg_root_module / CACHE_PATH
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(path)


def tf_lock_info(tg_root_module: OSPath) -> json.Value:
    with sh.cd(tg_root_module):
        lock_info = sh.json((LIB / "tf-lock-info-uncached",))
        assert isinstance(lock_info, dict)
        if lock_info["lock"]:
            path = lock_info["Path"]
            assert isinstance(path, str)
            cache_put(tg_root_module, path)
        else:
            lock_info.setdefault("Path", cache_get(tg_root_module))

    return lock_info


@UserError.handler
def main() -> ExitCode:
    with sh.quiet():
        import json

        print(json.dumps(tf_lock_info(OSPath.cwd())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
