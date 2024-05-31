#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Union

from lib.constants import TACOS_GHA_HOME
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath

TFLockFile = OSPath


@dataclass(frozen=True)
class TerraformerResult:
    GETSENTRY_SAC_OIDC: str
    SUDO_GCP_SERVICE_ACCOUNT: str
    tflock_files: set[OSPath]


def list_cached_tflock_files() -> list[TFLockFile]:
    import os
    from subprocess import check_output

    current_dir = os.getcwd()
    slices = check_output(
        (
            "find",
            current_dir,
            "-path",
            "*/.config/tf-lock-info/Path",
            "-print0",
        ),
        encoding="UTF-8",
    )
    return sorted([OSPath(slice) for slice in slices.split("\0")])


def list_terraformers() -> Generator[TerraformerResult]:
    """List all slices and the oidc provider and terraformer of that slice"""
    for tflock_file in list_cached_tflock_files():
        with sh.cd(tflock_file.parents[2]):
            oidc_provider = sh.stdout(
                (TACOS_GHA_HOME / "lib/getsentry-sac/oidc-provider",)
            )
            terraformer = sh.stdout(("sudo-gcp-service-account",))

            yield TerraformerResult(
                oidc_provider, terraformer, set([tflock_file])
            )


def terraformers() -> Generator[TerraformerResult]:
    """Which slices need to be unlocked?"""
    from collections import defaultdict

    by_terraformer: defaultdict[tuple[str, str], set[TFLockFile]] = (
        defaultdict(set)
    )

    for tf_result in list_terraformers():
        key = (
            tf_result.GETSENTRY_SAC_OIDC,
            tf_result.SUDO_GCP_SERVICE_ACCOUNT,
        )
        for tflock_file in tf_result.tflock_files:
            by_terraformer[key].add(tflock_file)

    for key in by_terraformer:
        oidc_provider, terraformer = key
        yield TerraformerResult(
            oidc_provider, terraformer, by_terraformer[key]
        )


def convert_terraform_result(
    result: TerraformerResult,
) -> Dict[str, Union[str, List[str]]]:
    """Convert TerraformerResult to a JSON-serializable dictionary"""
    return {
        "GETSENTRY_SAC_OIDC": result.GETSENTRY_SAC_OIDC,
        "SUDO_GCP_SERVICE_ACCOUNT": result.SUDO_GCP_SERVICE_ACCOUNT,
        # Convert each TopLevelTFModule in the set to a string, then convert the set to a list
        "tflock_files": [str(path) for path in result.tflock_files],
    }


def main() -> int:
    import json

    for result in terraformers():
        # use custom conversion here, because json doesn't like sets or OSPaths
        print(json.dumps(convert_terraform_result(result)))

    return 0


if __name__ == "__main__":
    exit(main())
