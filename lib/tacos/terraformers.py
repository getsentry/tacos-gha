#!/usr/bin/env python3.12
from __future__ import annotations

import dataclasses

# import typing
from dataclasses import dataclass
from typing import Iterable

from lib.constants import TACOS_GHA_HOME
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath


@dataclass(frozen=True)
class TerraformerResult:
    GETSENTRY_SAC_OIDC: str
    SUDO_GCP_SERVICE_ACCOUNT: str
    slices: list[OSPath]


def list_terraformers(
    slices: Iterable[OSPath],
) -> Generator[TerraformerResult]:
    """List all slices and the oidc provider and terraformer of that slice"""
    for slice in slices:
        with sh.cd(slice):

            ### from set-workload-identity-provider:
            # with-user-env "$TF_ROOT_MODULE" \
            #     "$TACOS_GHA_HOME/"lib/getsentry-sac/oidc-provider "$@" |
            #   gha-set-env GETSENTRY_SAC_OIDC \
            # ;

            oidc_provider = sh.stdout(
                (TACOS_GHA_HOME / "lib/getsentry-sac/oidc-provider",)
            )

            ### with-user-env "$TF_ROOT_MODULE" \
            ###     sudo-gcp-service-account |
            ###     gha-set-env SUDO_GCP_SERVICE_ACCOUNT \
            ### ;
            terraformer = sh.stdout(("sudo-gcp-service-account",))

            yield TerraformerResult(oidc_provider, terraformer, list([slice]))


def terraformers(slices: Iterable[OSPath]) -> Generator[TerraformerResult]:
    """Which slices need to be unlocked?"""
    from collections import defaultdict

    by_terraformer: defaultdict[tuple[str, str], list[OSPath]] = defaultdict(
        list
    )

    for tf_result in list_terraformers(slices):
        key = (
            tf_result.GETSENTRY_SAC_OIDC,
            tf_result.SUDO_GCP_SERVICE_ACCOUNT,
        )
        for slice in tf_result.slices:
            by_terraformer[key].append(slice)

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


def main() -> int:
    import fileinput
    import json

    slices = lines_to_paths(fileinput.input(encoding="utf-8"))

    for result in terraformers(slices):
        print(json.dumps(dataclasses.asdict(result)))

    return 0


if __name__ == "__main__":
    exit(main())
