from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException, status

# Set to 0 to disable expiry check (useful in development)
MAX_AUTH_AGE_SECONDS = int(os.getenv("AUTH_MAX_AGE", "300"))


def validate_init_data(raw_init_data: str, bot_token: str) -> Dict[str, Any]:
    """
    Validate Telegram WebApp initData string.
    Returns the parsed fields dict (with 'user' decoded from JSON).
    Raises HTTPException 401 on invalid or expired data.
    """
    try:
        params: Dict[str, str] = dict(parse_qsl(raw_init_data, keep_blank_values=True))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        ) from exc

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        )

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        )

    if MAX_AUTH_AGE_SECONDS > 0:
        auth_date = int(params.get("auth_date", "0"))
        if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "init_data_expired"},
            )

    # Decode nested user JSON
    user_raw = params.get("user", "{}")
    try:
        params["user"] = json.loads(unquote(user_raw))  # type: ignore[assignment]
    except json.JSONDecodeError:
        params["user"] = {}  # type: ignore[assignment]

    return params  # type: ignore[return-value]


def parse_authorization(authorization: str) -> Dict[str, Any]:
    """
    Parse Authorization header.
    Supports:
    - "tma <initData>"  — real Telegram WebApp
    - "tma debug"       — bypass when DEBUG_BYPASS_AUTH=1
    """
    if not authorization.startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        )
    raw = authorization[4:]

    # Dev bypass
    if raw == "debug" and os.getenv("DEBUG_BYPASS_AUTH"):
        return {
            "user": {
                "id": 999999999,
                "first_name": "Dev",
                "username": "devuser",
                "last_name": None,
            }
        }

    from src.config import settings

    return validate_init_data(raw, settings.bot_token)
