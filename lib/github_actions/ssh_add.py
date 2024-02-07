#!/usr/bin/env python3.12
from __future__ import annotations

from typing import Generator
from typing import Iterable
from typing import Iterator

from lib.sh import sh
from lib.user_error import UserError

SSH_KEY_BEGIN = "-----BEGIN OPENSSH PRIVATE KEY-----"
SSH_KEY_END = "-----END OPENSSH PRIVATE KEY-----"
Key = str


def stripped(lines: Iterable[str]) -> Generator[str, None, None]:
    for line in lines:
        line = line.strip()

        if line and not line.startswith("#"):
            yield line


def one_key(lines: Iterator[str]) -> Key | None:
    lines = stripped(lines)

    key: list[str]
    for line in lines:
        if line == SSH_KEY_BEGIN:
            key = [line]
            break
        else:
            raise UserError(f"Expecting start of key, got: {line}")
    else:
        return None

    for line in lines:
        key.append(line)
        if line == SSH_KEY_END:
            key.append("")
            return "\n".join(key)
    else:
        raise UserError("Got EOF before end of key")


def split_keys(lines: Iterable[str]) -> Generator[Key, None, None]:
    lines = iter(lines)
    while True:
        key = one_key(lines)
        if key is None:
            break
        else:
            yield key


def ssh_add(lines: Iterable[str]) -> None:
    for key in split_keys(lines):
        sh.run(("ssh-add", "-"), input=key)


def main() -> None:
    import sys

    ssh_add(sys.stdin)


if __name__ == "__main__":
    main()
