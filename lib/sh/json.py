from __future__ import annotations

from lib import json as JSON

from .constant import US_ASCII
from .core import lines
from .core import stdout
from .types import Command
from .types import Generator


def json(cmd: Command) -> JSON.Value:
    """Parse the (singular) json on a subprocess' stdout.

    >>> json(("echo", '{"a": "b", "c": 3}'))
    {'a': 'b', 'c': 3}
    """
    import json

    result: JSON.Value = json.loads(stdout(cmd))
    return result


def jq(cmd: Command, encoding: str = US_ASCII) -> Generator[JSON.Value]:
    """Yield each object from newline-delimited json on a subprocess' stdout.

    >>> tuple(jq(("seq", 3)))
    (1, 2, 3)
    """
    import json

    for line in lines(cmd, encoding=encoding):
        try:
            result: JSON.Value = json.loads(line)
        except Exception as error:
            raise ValueError(f"bad JSON:\n    {line}") from error
        else:
            yield result
