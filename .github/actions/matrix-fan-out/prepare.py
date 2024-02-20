#!/usr/bin/env python3
# Set artifact_name output, but also ensure matrix context appears at fan-in.
# note: stdout goes to GITHUB_ENV
from __future__ import annotations

import typing
from pathlib import Path
from subprocess import run
from typing import Literal

T = typing.TypeVar("T")
Generator = typing.Generator[T, None, None]

Key = str
Val = str
MatrixContext = dict[Key, Val]
StepName = str
StepsContext = dict[StepName, dict[Literal["outputs"], dict[Key, Val]]]

HERE = Path(__file__).resolve().parent


def step_outputs(steps: StepsContext) -> Generator[tuple[Path, Val | None]]:
    for step_name, step in sorted(steps.items()):
        del step_name
        outputs = sorted(step.get("outputs", {}).items())
        for key, val in outputs:
            if key.startswith("artifact."):
                yield Path(val), None
            else:
                yield Path(key), val


def mkdirp(path: Path) -> None:
    path.mkdir(exist_ok=True, parents=True)


def prepare(
    path: Path, matrix_context: str, steps_context: StepsContext
) -> None:
    mkdirp(path)
    for items in (
        ((Path("GHA_MATRIX_CONTEXT.json"), matrix_context),),
        step_outputs(steps_context),
    ):
        for subpath, val in items:
            if val is None:
                newpath = path / subpath
                mkdirp(newpath.parent)
                run(("cp", "-va", subpath, newpath), check=True, stdout=2)
            else:
                (path / subpath).write_text(val)


def get_artifact_name(matrix_context: str) -> str:
    import json

    matrix: MatrixContext = json.loads(matrix_context)

    result = "/".join(f"{key}={val}" for key, val in sorted(matrix.items()))

    return f"/({result})"


def set_artifact_name(path: Path, matrix_context: str) -> None:
    artifact_name = get_artifact_name(matrix_context)

    run(
        (HERE / "artifact-name.sh", path),
        input=artifact_name.encode(),
        check=True,
    )


def main() -> int:
    import json
    import os

    steps_context: StepsContext
    steps_context_data = os.environ["GHA_STEPS_CONTEXT"]
    if steps_context_data:
        steps_context = json.loads(steps_context_data)
    else:
        steps_context = {}
    matrix_context = os.environ["GHA_MATRIX_CONTEXT"]

    path = Path(os.environ["MATRIX_FAN_OUT_PATH"])

    prepare(path, matrix_context, steps_context)
    set_artifact_name(path, matrix_context)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
