"""nasty hack to convince pytest-doctest to capture stderr too"""
from __future__ import annotations

from contextlib import contextmanager

from _pytest import doctest

from lib.types import Callback
from lib.types import Generator

from . import hook


class DoctestItemWithCapture(doctest.DoctestItem):
    """Don't disable capture on macos."""

    def _disable_output_capturing_for_darwin(self):
        # The problem this was working around seems to be gone, now?
        pass


@contextmanager
def configured() -> Generator[None]:
    # nasty hack to override some default behavior of pytest-doctest
    import _pytest.doctest

    from lib.pytest.doctest import DoctestItemWithCapture

    DoctestItem = _pytest.doctest.DoctestItem
    setattr(_pytest.doctest, "DoctestItem", DoctestItemWithCapture)

    yield

    setattr(_pytest.doctest, "DoctestItem", DoctestItem)


pytest_configure: Callback[None]
pytest_unconfigure: Callback[None]
pytest_configure, pytest_unconfigure = hook.beforeafter(configured)
