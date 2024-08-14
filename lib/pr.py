from __future__ import annotations

from dataclasses import dataclass

from lib.sh import sh
from lib.types import URL


@dataclass(frozen=True)
class PR:
    url: URL

    def is_closed(self) -> bool:
        status = sh.stdout(
            ("gh", "pr", "view", self.url, "--json", "state", "--jq", ".state")
        )
        return status in ("CLOSED", "MERGED")
