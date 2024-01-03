from __future__ import annotations

import getpass
from pathlib import Path

from . import functions

### a few universally-valid variables:
USER = getpass.getuser()
NOW = functions.now()
TOP = Path(__file__).parents[1]
