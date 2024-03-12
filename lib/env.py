from __future__ import annotations

import contextlib

from lib.types import Environ as Environ
from lib.types import Generator


@contextlib.contextmanager
def fixed(environ: Environ) -> Generator[Environ]:
    """This context cannot affect the outer scope's environment."""
    orig = dict(environ)

    yield environ

    for var in set(orig).union(environ):
        if var in orig:
            environ[var] = orig[var]
        else:
            del environ[var]
