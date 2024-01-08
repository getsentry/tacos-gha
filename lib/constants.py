from __future__ import annotations

import getpass

from lib.types import OSPath
from lib.types import Path

from . import functions

### a few universally-valid variables:
USER = getpass.getuser()
NOW = functions.now()
REPO_TOP = OSPath(__file__).parents[1]
EMPTY_PATH = Path("")
