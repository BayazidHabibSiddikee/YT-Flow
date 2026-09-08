#!/usr/bin/env python3
"""
One-time YouTube OAuth flow to obtain + persist a refresh token.

Reads YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET from .env, then:
  1. Prints an authorization URL for the channel owner to visit.
  2. Runs a local callback server to catch the OAuth redirect.
  3. Exchanges the code for tokens and saves refresh token to .env
     (or to an optional --token-file).

Run once interactively. Afterwards uploads are fully automated via the
refresh token (no re-login).
"""
import argparse
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

DESKTOP_CLIENT_ID = "764086051850-6qr4p6gpi6hn506lt8tne00n78bg5rb2.apps.googleusercontent.com"  # noqa


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def save_token_to_env(refresh_token):
    if not ENV_FILE.exists():
        return False
    lines = []
    replaced = False
    for line in ENV_FILE.read_text().splitlines():
        if line.strip().startswith("YOUTUBE_REFRESH_TOKEN"):
            lines.append(f'YOUTUBE_REFRESH_TOKEN="{refresh_token}"')
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        lines.append(f'\nYOUTUBE_REFRESH_TOKEN="{refresh_token}"')
    ENV_FILE.write_text("\n".join(lines) + "\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Acquire a YouTube OAuth refresh token")
    parser.add_argument(
        "--token-file",
        default=None,
        help="Path to write the refresh token (default: add YOUTUBE_REFRESH_TOKEN to .env)",
    )
    parser.add_argument(
        "--client-id",
        default=None,
        help="Google OAuth client ID (default: YOUTUBE_CLIENT_ID or Client_ID_IZUKU from .env)",
    )
    parser.add_argument(
        "--client-secret",
        default=None,
        help="Google OAuth client secret (default: YOUTUBE_CLIENT_SECRET or Client_SECRET_IZUKU from .env)",
    )
    args = parser.parse_args()

    env = load_env()
    client_id = args.client_id or env.get("YOUTUBE_CLIENT_ID") or env.get("Client_ID_IZUKU")
    client_secret = (
        args.client_secret
        or env.get("YOUTUBE_CLIENT_SECRET")
        or env.get("Client_SECRET_IZUKU")
    )

    if not client_id or not client_secret:
        print(
            "[ERROR] YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET not found. "
            "Add them to .env or pass --client-id/--client-secret.",
            file=sys.stderr,
        )
        sys.exit(1)

    # LOCALHOST clients use a fixed-installed client id; the real secret still applies.
    installed_json = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
    }

    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    token_file = Path(args.token_file) if args.token_file else None
    if token_file and token_file.exists():
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(installed_json, SCOPES)
        creds = flow.run_local_server(port=0, open_browser=False, prompt="consent")
        print("\n[AUTH] Authorization succeeded.\n")

    print(f"[OK] Access token obtained (expires in {creds.expiry})")
    print(f"[OK] Refresh token: {creds.refresh_token}")

    if token_file:
        token_file.write_text(
            creds.to_json() if hasattr(creds, "to_json") else (
                '{"token": %r, "refresh_token": %r}' % (creds.token, creds.refresh_token)
            )
        )
        print(f"[OK] Saved credential JSON to {token_file}")
        # If we already wrote the full JSON, also drop the refresh token into .env
        if creds.refresh_token:
            save_token_to_env(creds.refresh_token)
    else:
        if creds.refresh_token:
            save_token_to_env(creds.refresh_token)
            print("[OK] YOUTUBE_REFRESH_TOKEN added to .env")
        else:
            print("[WARN] No refresh token returned (re-authorize if you want auto-renewal).")


if __name__ == "__main__":
    main()