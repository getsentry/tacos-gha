"""Define a 'cap1fd' pytest fixture which captures stdout/stderr combined."""

from __future__ import annotations

import contextlib
from io import FileIO
from typing import IO
from typing import Generator
from typing import Literal
from typing import TypeAlias
from typing import TypeVar

from _pytest.capture import CaptureBase
from _pytest.capture import CaptureFixture
from _pytest.capture import CaptureManager
from _pytest.capture import MultiCapture
from _pytest.capture import NoCapture
from _pytest.capture import (
    _CaptureMethod,  # pyright: ignore[reportPrivateUsage]; isort:skip
)
from _pytest.fixtures import SubRequest
from _pytest.fixtures import fixture

from lib.constants import UNSET
from lib.constants import Unset
from lib.sh import sh

T = TypeVar("T")

FD = int
STDIN: FD = 0
STDOUT: FD = 1
STDERR: FD = 2


class FDCapture(CaptureBase[str]):
    def __init__(  # pyright: ignore[reportMissingSuperCall]  # TODO: bugreport
        self, targetfd: FD, **_: object
    ):
        from os import dup
        from tempfile import TemporaryFile

        self.targetfd = targetfd

        self.tmpfile: FileIO = TemporaryFile(buffering=0)
        self.dest: IO[bytes] = self.tmpfile
        self.targetfd_save: FD = dup(targetfd)
        self.exitstack: contextlib.ExitStack = contextlib.ExitStack()

    def start(self) -> None:
        self.resume()

    def done(self) -> None:
        self.suspend()
        self.tmpfile.close()

    def suspend(self) -> None:
        self.exitstack.__exit__(None, None, None)

    def resume(self) -> None:
        self.exitstack.enter_context(
            sh.redirect(self.targetfd, self.dest.fileno())
        )

    def writeorg(self, data: str) -> None:
        """Write to original file descriptor."""
        import os

        os.write(self.targetfd_save, data.encode())

    def snap(self) -> str:
        self.tmpfile.seek(0)
        result = self.tmpfile.read()
        self.tmpfile.truncate(0)
        return result.decode()


class CombinedCapture(FDCapture):
    def __init__(self, targetfd: FD, *other_fds: FD):
        super().__init__(targetfd)
        self.other_fds = other_fds

    def resume(self) -> None:
        super().resume()
        for other_fd in self.other_fds:
            self.exitstack.enter_context(sh.redirect(other_fd, self.targetfd))


class CombinedTeeCapture(CombinedCapture):
    def resume(self) -> None:

        from subprocess import PIPE
        from subprocess import Popen

        # TODO: you'll probably want to rewrite this as a python thread someday
        tee = Popen(
            ("tee", "/dev/stderr"),
            stdin=PIPE,
            stdout=self.tmpfile,
            encoding=None,
            stderr=self.targetfd_save,
        )
        assert tee.stdin is not None

        self.dest: IO[bytes] = tee.stdin

        # TODO: apparently pytest calls resume() once per test during discovery?
        ### # This extra newline adds significant readability, because pytest
        ### # *prepends* newlines to its status lines, like an anarcho-nihilist.
        ### self.writeorg("\n")

        # FIXME: this is "right" but it causes stdio deadlock D:
        ### # the tee should live longer than the redirect, to avoid EPIPE
        ### self.exitstack.enter_context(tee)  # close, flush buffers, and wait

        super().resume()

        self.exitstack.enter_context(
            sh.redirect(self.targetfd, tee.stdin.fileno())
        )
        self.exitstack.enter_context(tee.stdin)  # close tee's stdin


# see xdist.plugin.parse_numprocesses
XdistNumProcesses: TypeAlias = (
    None | int | Literal["auto"] | Literal["logical"]
)


def get_captureclass(nproc: XdistNumProcesses) -> type[CaptureBase[str]]:

    def captureclass(fd: FD) -> CaptureBase[str]:
        if fd == 2:
            return NoCapture(-1)  # CombinedCapture, below, will handle stderr
        elif fd != 1:
            raise AssertionError("expected stdout", fd)
        elif nproc is None or (isinstance(nproc, int) and nproc < 2):
            # running tests in serial -- tee to orig stderr so we can watch
            return CombinedTeeCapture(1, 2)
        else:  # nproc in ("auto", "logical", 0) or nproc > 1
            # running tests in parallel -- supress unusable interleaved output
            return CombinedCapture(1, 2)

    captureclass.EMPTY_BUFFER = ""  # type:ignore

    # Callable[int, CaptureBase[str]] is *actually* fully compatible with
    # type[CaptureBase[str]], as long as the args exactly match
    return captureclass  # type: ignore


def get_multicapture(
    method: _CaptureMethod, nproc: XdistNumProcesses
) -> MultiCapture[str]:
    if method == "no":
        return MultiCapture(in_=None, out=None, err=None)

    else:
        captureclass = get_captureclass(nproc)
        return MultiCapture(in_=None, out=captureclass(1), err=captureclass(2))


class CombinedCaptureManager(CaptureManager):
    nproc: XdistNumProcesses | Unset = UNSET

    @classmethod
    def set_numprocesses(cls, nproc: XdistNumProcesses) -> None:
        cls.nproc = nproc

    def start_global_capturing(self) -> None:
        assert self._global_capturing is None
        assert self.nproc is not UNSET

        self._global_capturing = get_multicapture(self._method, self.nproc)
        self._global_capturing.start_capturing()


@fixture
def cap1fd(request: SubRequest) -> Generator[CaptureFixture[str], None, None]:
    r"""Enable text capturing of writes to stdout and stderr, combined.

    This enables accurate temporal interleaving of writes, at the cost of
    losing the ability to distinguish between out and err. This is often
    beneficical because:
        1. it's how users and logs will see the output, by default
        3. the temporal relationship between output and errors is highly
            relevant to users and to tests
        3. under test, combined longs are easier to understand and debug

    ``cap1fd.readouterr()`` will return combined output as `out` and
    empty-string as `err`.

    Returns an instance of :class:`CaptureFixture[str]`.

    Example:

    .. code-block:: python

        def test_system_echo(cap1fd):
            os.system('echo "hello"; echo ERROR >&2')
            captured = cap1fd.readouterr()
            assert captured.out == "hello\nERROR\n"
    """
    config = request.config
    nproc = config.option.numprocesses

    capman = config.pluginmanager.getplugin("capturemanager")
    assert isinstance(capman, CombinedCaptureManager), capman
    capman.set_numprocesses(nproc)

    capture_fixture = CaptureFixture(
        get_captureclass(nproc), request, _ispytest=True
    )
    try:
        capman.set_fixture(capture_fixture)
        capture_fixture._start()  # pyright: ignore[reportPrivateUsage]
        yield capture_fixture
    finally:
        capture_fixture.close()
        capman.unset_fixture()
