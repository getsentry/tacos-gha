from __future__ import annotations

import json
import sys
import time
from urllib.request import Request
from urllib.request import urlopen

from jwt import JWT
from jwt import jwk_from_pem

from lib.sh import sh

APP_ID = 696623
INSTALLATION_ID = 45043058
PEM_PATH = "op://Team Tacos gha dev/tacos-gha-reviewer.2024-01-08.private-key/private key"


def make_jwt() -> str:
    pem = sh.stdout(("op", "read", PEM_PATH))
    signing_key = jwk_from_pem(pem.encode("ascii"))

    payload = {
        # Issued at time
        "iat": int(time.time()),
        # JWT expiration time (10 minutes maximum)
        "exp": int(time.time()) + 600,
        # GitHub App's identifier
        "iss": APP_ID,
    }

    # Create JWT
    jwt_instance = JWT()
    return jwt_instance.encode(payload, signing_key, alg="RS256")


def get_installation_access_token(jwt: str) -> str:
    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {jwt}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = Request(url, method="POST", headers=headers)
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    token = data["token"]
    assert isinstance(str, token)
    return token
