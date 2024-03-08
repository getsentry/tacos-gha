from __future__ import annotations

import typing
from pathlib import PosixPath
from pathlib import PurePosixPath

T = typing.TypeVar("T")
Generator = typing.Generator[T, None, None]  # py313/PEP696 shim
Environ = typing.MutableMapping[str, str]
Callback = typing.Callable[[], T]
ExitCode = str | int | None
Line = str
Lines = typing.Iterable[Line]


class Path(PurePosixPath):
    EMPTY: typing.ClassVar[Path]
    DOT: typing.ClassVar[Path]

    @classmethod
    def cwd(cls, environ: Environ) -> typing.Self:
        return cls(environ["PWD"])


Path.EMPTY = Path("")
Path.DOT = Path(".")


class OSPath(PosixPath, Path):
    @classmethod
    def cwd(cls, environ: object = None) -> typing.Self:
        del environ
        return super().cwd()


class URL(str):
    __slots__ = ()

    def __repr__(self):
        return f"URL({super().__repr__()})"


Boolish = object  # I'd like to define this more strictly
