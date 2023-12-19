#!/usr/bin/env py.test
from __future__ import annotations

from _pytest.outcomes import XFailed as XFailed

# NOTE subclasses of XFailed explode.

# represent a deferred assertion
XFail = tuple[str, object]
XFails = list[XFail]
