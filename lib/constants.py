from __future__ import annotations

import getpass

from lib.types import OSPath

from . import functions

### a few universally-valid variables:
USER = getpass.getuser()
NOW = functions.now()
TACOS_GHA_HOME = OSPath(__file__).parents[1]
