#!/usr/bin/env -S python3.12 -P
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from lib import json
from lib.json import assert_dict_of_strings
from lib.sh import sh
from lib.types import Generator


class Color(str):
    def __new__(cls, object: object) -> Self:
        return super().__new__(cls, str(object).upper())


@dataclass(frozen=True)
class GithubLabel:
    name: str
    color: Color
    description: str
    repo: str

    @classmethod
    def from_json(cls, json: json.Value, repo: str) -> Self:
        label = assert_dict_of_strings(json)
        color = Color(label.pop("color"))
        return cls(repo=repo, color=color, **label)

    @classmethod
    def from_repo(cls, repo: str) -> Generator[Self]:
        for json in sh.jq((
            "gh",
            f"--repo={repo}",
            "label",
            "list",
            "--search=:taco:",
            "--json=name,description,color,createdAt",
            "--jq=sort_by(.createdAt)[] | del(.createdAt)",
        )):
            yield cls.from_json(json, repo)

    # CRUD
    def create(self) -> sh.Command:
        return (
            "gh",
            f"--repo={self.repo}",
            "label",
            "create",
            self.name,
            f"--color={self.color}",
            f"--description={self.description}",
        )

    def update(self) -> sh.Command:
        return (
            "gh",
            f"--repo={self.repo}",
            "label",
            "edit",
            self.name,
            f"--color={self.color}",
            f"--description={self.description}",
        )

    def delete(self) -> sh.Command:
        return (
            "gh",
            f"--repo={self.repo}",
            "label",
            "delete",
            "--yes",
            self.name,
        )


def get_label_config(repo: str) -> Generator[GithubLabel]:
    for json in sh.jq(("./etc/labels.jq", "--compact-output")):
        yield GithubLabel.from_json(json, repo)


def tacos_install_labels(repo: str) -> Generator[sh.Command]:
    config = iter(tuple(get_label_config(repo)))
    labels = iter(tuple(GithubLabel.from_repo(repo)))
    expected = next(config, None)
    sh.comment("Expected:", getattr(expected, "name", None))

    for actual in labels:
        sh.comment("Actual:", actual.name)
        if not actual.name.startswith(":taco:"):
            continue

        if expected == actual:
            # that's good, now let's scheck for the next label
            sh.comment("Good.")
            expected = next(config, None)
            sh.comment("Expected:", getattr(expected, "name", None))
        elif expected is None:
            yield actual.delete()
        elif expected.name == actual.name:
            yield expected.update()
            expected = next(config, None)
            sh.comment("Expected:", getattr(expected, "name", None))
        else:
            yield actual.delete()

    if expected is not None:
        yield (("sleep", "1"))
        yield expected.create()

    for label in config:
        sh.comment("Expected:", label.name)
        yield (("sleep", "1"))
        yield label.create()


def main() -> int:
    from sys import argv

    repo = argv[1]

    print(
        """\
# This script only prints commands.
# To commit, pipe to a shell:  | sh
set -ex"""
    )

    for command in tacos_install_labels(repo):
        print(sh.quote(command))

    return 0


if __name__ == "__main__":
    exit(main())
