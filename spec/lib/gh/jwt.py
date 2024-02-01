from __future__ import annotations

from datetime import datetime

import jwt

from lib.functions import now as mknow


class JWT(str):
    # github JWT has a maximum expiration time of 10 minutes
    def __new__(
        cls,
        issuer: str,
        key: str,
        now: datetime | None = None,
        expiry_minutes: int = 10,
    ) -> JWT:
        if now is None:
            now = mknow()

        # Create JWT
        return super().__new__(
            cls,
            jwt.encode(
                payload=cls.payload(
                    issuer, now, expiry_minutes=expiry_minutes
                ),
                key=key,
                # https://auth0.com/blog/rs256-vs-hs256-whats-the-difference/
                # > RS256 is the recommended algorithm when signing your JWTs. It is
                # > more secure, and you can rotate keys quickly if they are compromised.
                # > (Auth0 signs JWTs with RS256 by default).
                algorithm="RS256",
            ),
        )

    @staticmethod
    def payload(
        issuer: str, now: datetime, *, expiry_minutes: float
    ) -> dict[str, int | str]:
        timestamp = int(now.timestamp())
        return {
            # Issued at
            "iat": timestamp,
            # expires at
            "exp": timestamp + int(expiry_minutes * 60),
            # issuer
            "iss": issuer,
        }
