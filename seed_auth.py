#!/usr/bin/env python3
"""Seed the bridge auth.json from a raw OpenAI OAuth access token — no browser login.

Prism's session cookie `prism_oai_access_token` accepts the same JWT the OAuth
flow issues, so an account from a token pool can be dropped in directly and
re-seeded any time the token refreshes (no 10-day manual re-login).

Usage:
    python seed_auth.py <access_token> [auth.json path]
"""
import base64
import json
import sys
import time
from pathlib import Path


def claims(token: str) -> dict:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part))
    except Exception:
        return {}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    token = sys.argv[1].strip()
    auth_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / ".prism-playwright-profile" / "auth.json"
    payload = claims(token)
    auth = payload.get("https://api.openai.com/auth", {}) or {}
    user_id = auth.get("chatgpt_user_id") or "user-unknown"
    exp = payload.get("exp") or 0
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "cookie": f"prism_oai_access_token={token}",
        "updated_at": int(time.time()),
        "user_id": user_id,
        "expires_at": exp,
        "plan": auth.get("plan_type") or auth.get("chatgpt_plan_type"),
        "email": payload.get("email"),
    }
    auth_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
    left = (exp - time.time()) / 3600 if exp else -1
    print(f"auth.json -> {auth_file}")
    print(f"user {user_id} plan {record['plan']} token expires in {left:.1f}h")


if __name__ == "__main__":
    main()
