from __future__ import annotations

import pytest

from .. import cap1fd


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--collectonly-json",
        action="store_true",
        help="Print test items to json, on stdout",
    )


def pytest_collection_finish(session: pytest.Session) -> None:
    if not session.config.option.collectonly_json:
        return

    session.config.option.collectonly = True

    tmp = session.config.pluginmanager.get_plugin("capturemanager")
    assert tmp is not None
    capman: cap1fd.CombinedCaptureManager = tmp
    del tmp

    assert capman.stdout is not cap1fd.UNSET

    import json
    from os import fdopen

    json.dump(
        [f"{item.path}::{item.name}" for item in session.items],
        fdopen(capman.stdout, "w"),
        indent=2,
    )
