from __future__ import annotations


class XFailed(AssertionError):
    pass


# represent a deferred assertion
XFail = tuple[str, object]
XFails = list[XFail]
