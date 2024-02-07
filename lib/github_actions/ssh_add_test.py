from __future__ import annotations

from io import StringIO

import pytest

from lib.user_error import UserError

from .ssh_add import SSH_KEY_BEGIN
from .ssh_add import SSH_KEY_END
from .ssh_add import one_key
from .ssh_add import split_keys

KEY1 = f"""\
{SSH_KEY_BEGIN}
xyz key1
{SSH_KEY_END}
"""

KEY2 = f"""\
{SSH_KEY_BEGIN}
abc key2
{SSH_KEY_END}
"""

KEYS = f"""

# comments!
{KEY1}

  {KEY2}

# other comment
"""


class DescribeSplitKeys:
    def it_does(self) -> None:
        lines = iter(StringIO(f"""

# comments!
{KEY1}

  {KEY2}

# other comment
"""))
        keys = split_keys(lines)

        assert tuple(keys) == (KEY1, KEY2)


class DescribeOneKey:
    def it_gets_singular_keys(self) -> None:
        lines = iter(StringIO(KEYS))
        assert one_key(lines) == KEY1
        assert one_key(lines) == KEY2
        assert one_key(lines) == None

    def it_notices_eof_before_end(self) -> None:
        lines = iter(StringIO(KEY1[:-30]))

        with pytest.raises(UserError) as exc:
            one_key(lines)
        assert exc.value.message == "Got EOF before end of key"

    def it_notices_junk(self) -> None:
        lines = iter(StringIO("oh, hi!"))
        with pytest.raises(UserError) as exc:
            one_key(lines)
        assert exc.value.message == "Expecting start of key, got: oh, hi!"
