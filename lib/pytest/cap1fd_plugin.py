from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING
from typing import Generator

from _pytest.capture import CaptureManager
from _pytest.capture import MultiCapture
from _pytest.config import hookimpl

from .cap1fd import CombinedFDCapture

if TYPE_CHECKING:
    from _pytest.capture import (
        _CaptureMethod,  # pyright: ignore[reportPrivateUsage]; isort:skip
    )


def _get_multicapture(method: _CaptureMethod) -> MultiCapture[str]:
    if method == "no":
        return MultiCapture(in_=None, out=None, err=None)
    else:
        return MultiCapture(
            in_=None, out=CombinedFDCapture(1), err=CombinedFDCapture(2)
        )


class MyCaptureManager(CaptureManager):
    def start_global_capturing(self) -> None:
        assert self._global_capturing is None
        self._global_capturing = _get_multicapture(self._method)
        self._global_capturing.start_capturing()


UNSET = object()
Vars = dict[str, object]


@contextlib.contextmanager
def patched(obj: object, **attrs: object) -> Generator[Vars, None, None]:
    oldattrs: dict[str, object] = {}
    for attr, value in attrs.items():
        oldattrs[attr] = getattr(obj, attr, UNSET)
        setattr(obj, attr, value)

    try:
        yield oldattrs

    finally:
        for attr, value in oldattrs.items():
            if value is UNSET:
                delattr(obj, attr)
            else:
                setattr(obj, attr, value)


@hookimpl(hookwrapper=True)
def pytest_load_initial_conftests() -> Generator[None, None, None]:
    import _pytest.capture

    with patched(_pytest.capture, CaptureManager=MyCaptureManager):
        yield
