"""Write a read-only snapshot of every account in the configured Enable Banking sessions."""

import base64
import datetime as dt
import json
import os
import pathlib
import time

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

API = "https://api.enablebanking.com"
SECRETS = pathlib.Path(os.environ.get("SECRETS_DIR", "/etc/bank-sync"))
OUT = pathlib.Path(os.environ.get("OUT", "/data/snapshot.json"))
DAYS = int(os.environ.get("DAYS", "90"))

app_id = (SECRETS / "app-id").read_text().strip()
key = serialization.load_pem_private_key((SECRETS / "private-key").read_bytes(), password=None)


def b64(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode() if isinstance(data, dict) else data).rstrip(b"=")


def token():
    now = int(time.time())
    header = {"typ": "JWT", "alg": "RS256", "kid": app_id}
    claims = {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": now, "exp": now + 300}
    signing_input = b64(header) + b"." + b64(claims)
    return (signing_input + b"." + b64(key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256()))).decode()


def get(path, **params):
    r = requests.get(API + path, params=params, headers={"Authorization": f"Bearer {token()}"}, timeout=60)
    r.raise_for_status()
    return r.json()


def transactions(uid, date_from):
    out, params = [], {"date_from": date_from}
    while True:
        page = get(f"/accounts/{uid}/transactions", **params)
        out += page.get("transactions") or []
        if not page.get("continuation_key"):
            return out
        params["continuation_key"] = page["continuation_key"]


def main():
    date_from = (dt.date.today() - dt.timedelta(days=DAYS)).isoformat()
    snapshot = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "sessions": []}
    # Logs carry the session index only, never a bank or account identifier.
    for i, s in enumerate(json.loads((SECRETS / "sessions").read_text())):
        entry = {"bank": s["bank"], "accounts": []}
        try:
            session = get(f"/sessions/{s['session_id']}")
            entry.update(status=session["status"], valid_until=session["access"]["valid_until"])
            for uid in session["accounts"]:
                entry["accounts"].append(
                    {
                        "details": get(f"/accounts/{uid}/details"),
                        "balances": get(f"/accounts/{uid}/balances")["balances"],
                        "transactions": transactions(uid, date_from),
                    }
                )
            print(f"session {i}: {session['status']}, {len(entry['accounts'])} account(s)")
        except requests.HTTPError as e:
            entry.update(status="stale", error=f"HTTP {e.response.status_code}")
            print(f"session {i}: HTTP {e.response.status_code}")
        snapshot["sessions"].append(entry)

    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(snapshot, indent=1))
    tmp.replace(OUT)


main()
