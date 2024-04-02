#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import List
from typing import Union

from lib.constants import TACOS_GHA_HOME
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath

from .dependent_slices import TFCategorized
from .dependent_slices import TopLevelTFModule


@dataclass(frozen=True)
class TerraformerResult:
    GETSENTRY_SAC_OIDC: str
    SUDO_GCP_SERVICE_ACCOUNT: str
    slices: set[TopLevelTFModule]


def list_terraformers() -> Generator[TerraformerResult]:
    """List all slices and the oidc provider and terraformer of that slice"""
    for slice in sorted(TFCategorized.from_git().slices):
        with sh.cd(slice):
            oidc_provider = sh.stdout(
                (TACOS_GHA_HOME / "lib/getsentry-sac/oidc-provider",)
            )
            terraformer = sh.stdout(("sudo-gcp-service-account",))

            yield TerraformerResult(oidc_provider, terraformer, set([slice]))


def terraformers() -> Generator[TerraformerResult]:
    """Which slices need to be unlocked?"""
    from collections import defaultdict

    by_terraformer: defaultdict[tuple[str, str], set[TopLevelTFModule]] = (
        defaultdict(set)
    )

    for tf_result in list_terraformers():
        key = (
            tf_result.GETSENTRY_SAC_OIDC,
            tf_result.SUDO_GCP_SERVICE_ACCOUNT,
        )
        for slice in tf_result.slices:
            by_terraformer[key].add(slice)

    for key in by_terraformer:
        oidc_provider, terraformer = key
        yield TerraformerResult(
            oidc_provider, terraformer, by_terraformer[key]
        )


def lines_to_paths(lines: Iterable[str]) -> Generator[OSPath]:
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield OSPath(line)


def convert_terraform_result(
    result: TerraformerResult,
) -> Dict[str, Union[str, List[str]]]:
    """Convert TerraformerResult to a JSON-serializable dictionary"""
    return {
        "GETSENTRY_SAC_OIDC": result.GETSENTRY_SAC_OIDC,
        "SUDO_GCP_SERVICE_ACCOUNT": result.SUDO_GCP_SERVICE_ACCOUNT,
        # Convert each OSPath in the set to a string, then convert the set to a list
        "slices": [str(path) for path in result.slices],
    }


def main() -> int:
    import json

    for result in terraformers():
        # use custom conversion here, because json doesn't like sets or OSPaths
        print(json.dumps(convert_terraform_result(result)))

    return 0


if __name__ == "__main__":
    exit(main())
