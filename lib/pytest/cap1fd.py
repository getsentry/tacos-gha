"""Define a 'cap1fd' pytest fixture which captures stdout/stderr combined."""
from __future__ import annotations

import contextlib
from io import FileIO
from typing import Generator

from _pytest.capture import CaptureBase
from _pytest.capture import CaptureFixture
from _pytest.capture import CaptureManager
from _pytest.capture import NoCapture
from _pytest.fixtures import SubRequest
from _pytest.fixtures import fixture

from lib.sh import sh

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
            sh.redirect(self.targetfd, self.tmpfile.fileno())
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


class NoopCapture(FDCapture):
    def resume(self) -> None:
        pass


class CombinedFDCapture(CaptureBase[str]):
    EMPTY_BUFFER: str = ""
    capture: CaptureBase[str]

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self, targetfd: FD
    ):
        if targetfd == 1:
            self.capture = CombinedCapture(targetfd, STDERR)
        elif targetfd == 2:
            self.capture = NoCapture(targetfd)
        else:
            raise ValueError(targetfd)

    def start(self) -> None:
        self.capture.start()

    def done(self) -> None:
        self.capture.done()

    def suspend(self) -> None:
        self.capture.suspend()

    def resume(self) -> None:
        self.capture.resume()

    def writeorg(self, data: str) -> None:
        self.capture.writeorg(data)

    def snap(self) -> str:
        return self.capture.snap()


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
    capman = request.config.pluginmanager.getplugin("capturemanager")
    assert isinstance(capman, CaptureManager), capman
    capture_fixture = CaptureFixture(
        CombinedFDCapture, request, _ispytest=True
    )
    try:
        capman.set_fixture(capture_fixture)
        capture_fixture._start()  # pyright: ignore[reportPrivateUsage]
        yield capture_fixture
    finally:
        capture_fixture.close()
        capman.unset_fixture()
