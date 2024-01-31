from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import NewType
from typing import Self
from urllib.request import Request
from urllib.request import urlopen

from lib.functions import one
from lib.parse import Parse
from lib.sh import sh

from .jwt import JWT
from .types import URL

InstallationToken = NewType("InstallationToken", str)


@dataclass(frozen=True)
class Installation:
    id: str
    app: str
    secret: str

    @classmethod
    def from_1password(cls, op_url: URL) -> Self:
        id = one(sh.lines(("op", "read", op_url)))

        app = Parse(op_url).before.last("/", "/")
        app_id = one(sh.lines(("op", "read", f"{app}/id")))
        app_secret = sh.stdout(("op", "read", f"{app}/private key"))

        return cls(id, app_id, app_secret)

    def token(
        self, jwt: JWT | None = None, now: datetime | None = None
    ) -> InstallationToken:
        if jwt is None:
            jwt = self.jwt(now)
        url = (
            f"https://api.github.com/app/installations/{self.id}/access_tokens"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        req = Request(url, method="POST", headers=headers)
        with urlopen(req) as resp:
            data = json.loads(resp.read())
        token = data["token"]
        assert isinstance(token, str)
        return InstallationToken(token)

    def jwt(self, now: datetime | None = None) -> JWT:
        return JWT(issuer=self.app, key=self.secret, now=now)
