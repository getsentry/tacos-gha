from __future__ import annotations

import pytest
from pytest import fixture
from typing_extensions import Generator

from manual_tests.lib import slice
from manual_tests.lib import tacos_demo


@fixture
def test_name(request: pytest.FixtureRequest) -> str:
    assert isinstance(
        request.node, pytest.Item  # pyright:ignore[reportUnknownMemberType]
    )
    module_path = request.node.path  # path to the test's module file
    return module_path.with_suffix("").name


@fixture
def slices() -> slice.Slices:
    return slice.random()


@fixture
def pr(
    test_name: str, slices: slice.Slices
) -> Generator[tacos_demo.PR, None, None]:
    with tacos_demo.PR.opened_for_test(test_name, slices) as result:
        yield result
