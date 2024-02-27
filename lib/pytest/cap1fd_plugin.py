from __future__ import annotations

from typing import Generator

from _pytest.config import Config
from _pytest.config import hookimpl

from lib.patched import patched

from .cap1fd import CombinedCaptureManager


@hookimpl(hookwrapper=True)
def pytest_load_initial_conftests(
    early_config: Config,
) -> Generator[None, None, None]:
    nproc = early_config.known_args_namespace.numprocesses
    CombinedCaptureManager.set_numprocesses(nproc)

    import _pytest.capture

    with patched(_pytest.capture, CaptureManager=CombinedCaptureManager):
        yield
