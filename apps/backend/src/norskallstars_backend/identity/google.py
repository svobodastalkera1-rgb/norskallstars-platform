"""Pinned Google key origin and bounded verification; no user-controlled key URLs."""

import asyncio
import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWK

JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"


class GoogleVerificationError(Exception):
    pass


@dataclass(frozen=True)
class GoogleClaims:
    subject: str
    email: str
    nonce: str
    authoritative_email: bool


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


class GoogleVerifier:
    def __init__(self) -> None:
        self.keys: dict[str, PyJWK] = {}
        self.until = 0.0
        self.last_fetch = -60.0
        self.lock = asyncio.Lock()

    def fetch_keys(self) -> dict[str, PyJWK]:
        # No ambient proxies, redirects or caller-controlled destinations/CA settings.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(JWKS_URL, timeout=3) as response:  # noqa: S310 -- constant HTTPS origin
            payload = response.read(65537)
        if len(payload) > 65536:
            raise GoogleVerificationError
        document = json.loads(payload)
        if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
            raise GoogleVerificationError
        if not 1 <= len(document["keys"]) <= 10:
            raise GoogleVerificationError
        keys: dict[str, PyJWK] = {}
        for item in document["keys"]:
            if not isinstance(item, dict) or item.get("kty") != "RSA" or item.get("use") != "sig":
                raise GoogleVerificationError
            kid = item.get("kid")
            if not isinstance(kid, str) or not 1 <= len(kid) <= 128 or kid in keys:
                raise GoogleVerificationError
            key = PyJWK.from_dict(item, algorithm="RS256")
            if key.key.key_size < 2048:
                raise GoogleVerificationError
            keys[kid] = key
        return keys

    async def verify(self, encoded: str, client_id: str) -> GoogleClaims:
        try:
            header = jwt.get_unverified_header(encoded)
            kid = header.get("kid")
            if header.get("alg") != "RS256" or not isinstance(kid, str) or len(kid) > 128:
                raise GoogleVerificationError
            async with self.lock:
                now = time.monotonic()
                if now >= self.until or kid not in self.keys:
                    if now - self.last_fetch < 30:
                        raise GoogleVerificationError
                    self.last_fetch = now
                    keys = await asyncio.to_thread(self.fetch_keys)
                    self.keys, self.until = keys, now + 300
                key = self.keys.get(kid)
            if key is None:
                raise GoogleVerificationError
            claims = jwt.decode(
                encoded,
                key.key,
                algorithms=["RS256"],
                audience=client_id,
                options={"require": ["exp", "iat", "iss", "sub", "aud", "nonce", "email"]},
                leeway=10,
            )
            if type(claims["iat"]) is not int or type(claims["exp"]) is not int:
                raise GoogleVerificationError
            if claims["exp"] <= claims["iat"] or claims["exp"] - claims["iat"] > 7200:
                raise GoogleVerificationError
            if time.time() - claims["iat"] > 600:
                raise GoogleVerificationError
            if claims["iss"] not in ("https://accounts.google.com", "accounts.google.com"):
                raise GoogleVerificationError
            if isinstance(claims["aud"], list) or claims.get("azp", client_id) != client_id:
                raise GoogleVerificationError
            if claims.get("email_verified") is not True:
                raise GoogleVerificationError
            if not isinstance(claims["sub"], str) or not 1 <= len(claims["sub"]) <= 255:
                raise GoogleVerificationError
            if not isinstance(claims["nonce"], str) or not 32 <= len(claims["nonce"]) <= 512:
                raise GoogleVerificationError
            from norskallstars_backend.identity.security import normalize_email

            email = normalize_email(claims["email"])
            hd = claims.get("hd")
            authoritative = email.endswith("@gmail.com") or (isinstance(hd, str) and bool(hd))
            return GoogleClaims(claims["sub"], email, claims["nonce"], authoritative)
        except Exception:
            # Never leak JWT, provider response, network destination details or parser exceptions.
            raise GoogleVerificationError from None
