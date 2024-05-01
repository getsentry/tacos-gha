from __future__ import annotations

from subprocess import CalledProcessError

from lib.user_error import UserError


class ShError(UserError, CalledProcessError):
    pass
