"""Small API-key authentication and role authorization boundary."""

import hmac
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal, cast

from fastapi import HTTPException, Request, status

Role = Literal["investigator", "operator", "admin"]


@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity and assigned role."""

    role: Role


class ApiKeyAuthenticator:
    """Authenticate bearer keys from a deployment-provided key map."""

    def __init__(self, keys: dict[str, Role]) -> None:
        self._keys = keys

    @classmethod
    def from_environment(cls) -> "ApiKeyAuthenticator":
        """Read `SENTINEL_API_KEYS=key:role,key:role` without logging secrets."""

        raw = os.getenv("SENTINEL_API_KEYS", "")
        keys: dict[str, Role] = {}
        for item in raw.split(","):
            if not item or ":" not in item:
                continue
            key, role = item.split(":", 1)
            if role in {"investigator", "operator", "admin"} and key:
                keys[key] = cast(Role, role)
        return cls(keys)

    @property
    def enabled(self) -> bool:
        return bool(self._keys)

    def authenticate(self, request: Request) -> Principal:
        """Return a principal or raise a standards-compatible HTTP error."""

        if not self.enabled:
            return Principal(role="admin")
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        for key, role in self._keys.items():
            if hmac.compare_digest(token, key):
                return Principal(role=role)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def require(self, role: Role) -> Callable[[Request], Awaitable[Principal]]:
        """Build a FastAPI dependency enforcing the requested minimum role."""

        rank = {"investigator": 1, "operator": 2, "admin": 3}

        async def dependency(request: Request) -> Principal:
            principal = self.authenticate(request)
            if rank[principal.role] < rank[role]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
                )
            return principal

        return dependency
