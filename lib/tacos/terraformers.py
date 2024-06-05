#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lib import json
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

    def to_json(self) -> json.Value:
        return {
            "GETSENTRY_SAC_OIDC": self.GETSENTRY_SAC_OIDC,
            "SUDO_GCP_SERVICE_ACCOUNT": self.SUDO_GCP_SERVICE_ACCOUNT,
            # Convert each TopLevelTFModule in the set to a string, then convert the set to a list
            "slices": [str(path) for path in self.slices],
        }


def get_cached_slices() -> Iterable[TopLevelTFModule]:
    """List terraform/grunt slices that have a cached tflock path.

    Slices without such a file have never been locked.
    """
    for slice in sorted(TFCategorized.from_git().slices):
        if OSPath(slice / ".config/tf-lock-info/Path").exists():
            yield slice


def list_terraformers(
    slices: Iterable[TopLevelTFModule],
) -> Iterable[TerraformerResult]:
    """List unlockable slices and the oidc provider and terraformer of that slice"""
    for slice in slices:
        with sh.cd(OSPath(slice)):
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

    slices = get_cached_slices()
    for tf_result in list_terraformers(slices):
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


def main() -> int:
    import json

    for result in terraformers():
        # use custom conversion here, because json doesn't like sets or OSPaths
        print(json.dumps(result.to_json()))

    return 0


if __name__ == "__main__":
    exit(main())
