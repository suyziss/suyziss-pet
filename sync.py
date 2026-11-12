#!/usr/bin/env python3
"""Encrypted GitHub backup/restore for Suyziss Pet."""
from __future__ import annotations

import base64
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SAVE_FILE = DATA_DIR / "pet.json"
STATE_FILE = DATA_DIR / "sync_state.json"
CONFIG_DIR = Path.home() / ".config" / "suyziss-pet"
TOKEN_FILE = CONFIG_DIR / "github_token"
REPO = "suyziss/suyziss-pet"
REMOTE_PATH = "cloud/saves/main.json.enc"
API_BASE = "https://api.github.com"


class SyncError(Exception):
    pass


def read_token() -> str:
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        return env_token.strip()
    if not TOKEN_FILE.exists():
        raise SyncError("No GitHub token. Run: python sync.py setup")
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def request(method: str, path: str, token: str, payload: dict | None = None):
    url = API_BASE + path
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "Suyziss-Pet/1.0")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if exc.code == 404:
            return None
        if exc.code == 409:
            raise SyncError("GitHub reported a conflict. Pull the latest save and retry.") from exc
        if exc.code == 401:
            raise SyncError("GitHub token is invalid or expired. Run setup again.") from exc
        if exc.code == 403:
            raise SyncError("GitHub denied access. Check token repository access and Contents read/write permission.") from exc
        raise SyncError(f"GitHub API error {exc.code}: {detail[:300]}") from exc
    except urllib.error.URLError as exc:
        raise SyncError(f"Network error: {exc.reason}") from exc


def derive_fernet(passphrase: str, salt: bytes) -> Fernet:
    if len(passphrase) < 10:
        raise SyncError("Use a passphrase of at least 10 characters.")
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
    return Fernet(key)


def encrypt(data: bytes, passphrase: str) -> str:
    import secrets
    salt = secrets.token_bytes(16)
    token = derive_fernet(passphrase, salt).encrypt(data)
    envelope = {
        "format": "suyziss-pet-encrypted-v1",
        "kdf": "scrypt-n16384-r8-p1",
        "salt": base64.b64encode(salt).decode("ascii"),
        "ciphertext": token.decode("ascii"),
    }
    return json.dumps(envelope, separators=(",", ":"))


def decrypt(envelope_text: str, passphrase: str) -> bytes:
    try:
        envelope = json.loads(envelope_text)
        if envelope.get("format") != "suyziss-pet-encrypted-v1":
            raise SyncError("Unknown backup format.")
        salt = base64.b64decode(envelope["salt"], validate=True)
        token = envelope["ciphertext"].encode("ascii")
        return derive_fernet(passphrase, salt).decrypt(token)
    except InvalidToken as exc:
        raise SyncError("Wrong passphrase or damaged encrypted backup.") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise SyncError("Encrypted backup is malformed.") from exc


def read_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(sha: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"remote_sha": sha}, indent=2) + "\n", encoding="utf-8")


def get_remote(token: str):
    from urllib.parse import quote
    path = f"/repos/{REPO}/contents/{quote(REMOTE_PATH, safe='/')}"
    return request("GET", path, token)


def setup() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token = getpass.getpass("GitHub fine-grained token (input hidden): ").strip()
    if not token:
        raise SyncError("Token cannot be empty.")
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass
    me = request("GET", "/user", token)
    print(f"GitHub authentication OK: {me.get('login', 'account')}")
    print(f"Token stored in {TOKEN_FILE} with restricted local permissions.")


def push() -> None:
    if not SAVE_FILE.exists():
        raise SyncError("No local save found. Run python pet.py once first.")
    token = read_token()
    remote = get_remote(token)
    state = read_state()
    remote_sha = remote.get("sha") if remote else None

    if remote and not state.get("remote_sha"):
        raise SyncError("A cloud save already exists but this device has no sync baseline. Run pull first.")
    if remote and state.get("remote_sha") != remote_sha:
        raise SyncError("Cloud save changed since this device last synced. Run pull first; local changes were not uploaded.")
    if not remote and state.get("remote_sha"):
        raise SyncError("Cloud save is missing although this device has a previous sync record. Refusing to recreate it automatically.")

    first = getpass.getpass("Backup passphrase (hidden): ")
    confirm = getpass.getpass("Confirm passphrase: ")
    if first != confirm:
        raise SyncError("Passphrases do not match.")
    plaintext = SAVE_FILE.read_bytes()
    encrypted = encrypt(plaintext, first)
    from urllib.parse import quote
    path = f"/repos/{REPO}/contents/{quote(REMOTE_PATH, safe='/')}"
    payload = {
        "message": "Update encrypted Suyziss Pet backup",
        "content": base64.b64encode(encrypted.encode("utf-8")).decode("ascii"),
    }
    if remote:
        payload["sha"] = remote_sha
    result = request("PUT", path, token, payload)
    new_sha = result.get("content", {}).get("sha")
    if not new_sha:
        raise SyncError("Upload response did not include a file SHA; verify cloud status before retrying.")
    write_state(new_sha)
    print("Encrypted backup uploaded successfully.")
    print("Keep your passphrase safe; it is required to restore the save.")


def pull() -> None:
    token = read_token()
    remote = get_remote(token)
    if not remote:
        raise SyncError("No cloud save exists yet. Push a save from your first device.")
    if SAVE_FILE.exists():
        answer = input("Replace the existing local save? Type YES to continue: ").strip()
        if answer != "YES":
            print("Restore cancelled.")
            return
    first = getpass.getpass("Backup passphrase (hidden): ")
    import urllib.parse
    content = remote.get("content", "")
    if remote.get("encoding") == "base64":
        encoded = base64.b64decode(content).decode("utf-8")
    else:
        # GitHub may omit content for large files; fetch the download URL.
        download_url = remote.get("download_url")
        if not download_url:
            raise SyncError("GitHub did not return backup content.")
        with urllib.request.urlopen(download_url, timeout=25) as response:
            encoded = response.read().decode("utf-8")
    plaintext = decrypt(encoded, first)
    parsed = json.loads(plaintext.decode("utf-8"))
    if not isinstance(parsed, dict) or "name" not in parsed or "level" not in parsed:
        raise SyncError("Decrypted data does not look like a Suyziss Pet save.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = SAVE_FILE.with_suffix(".restore.tmp")
    temp.write_bytes(plaintext)
    temp.replace(SAVE_FILE)
    write_state(remote["sha"])
    print(f"Restored {parsed.get('name', 'your pet')} (level {parsed.get('level', '?')}).")


def status() -> None:
    remote = get_remote(read_token())
    if not remote:
        print("No cloud backup found yet.")
        return
    print("Encrypted cloud backup exists.")
    print(f"Last GitHub update: {remote.get('updated_at', 'unknown')}")
    print(f"Remote file SHA: {remote.get('sha', 'unknown')}")
    local_sha = read_state().get("remote_sha")
    print("This device is synced to that version." if local_sha == remote.get("sha") else "This device has no matching sync baseline; pull before pushing.")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"setup", "push", "pull", "status"}:
        print("Usage: python sync.py {setup|push|pull|status}")
        return 2
    try:
        {"setup": setup, "push": push, "pull": pull, "status": status}[sys.argv[1]]()
        return 0
    except (SyncError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
