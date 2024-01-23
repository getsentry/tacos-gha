from __future__ import annotations

import typing
from pathlib import PosixPath
from pathlib import PurePosixPath

# mypy won't ignore `parent: Dir` otherwise:
# mypy: disable-error-code="assignment"


T = typing.TypeVar("T")
Generator = typing.Generator[T, None, None]  # py313/PEP696 shim
Environ = typing.MutableMapping[str, str]
Callback = typing.Callable[[], T]

Dir = typing.NewType("Dir", "Path")


class Path(PurePosixPath):
    parent: Dir

    # optimization: save 50% in dependent-slices by eagerly caching Path.parent
    __slots__ = ("parent",)

    def __init__(self, *_: object):
        super().__init__()
        self.parent = Dir(super().parent)  # pyright: ignore

    @classmethod
    def cwd(cls, environ: Environ) -> typing.Self:
        return cls(environ["PWD"])


class OSPath(PosixPath, Path):
    @classmethod
    def cwd(cls, environ: object = None) -> typing.Self:
        del environ
        return super().cwd()
