#!/usr/bin/env python3
"""Edvertico viewer app: lock (encrypt) the app data for GitHub.

Nothing secret is ever written into the repo. The data key and the
ID/password list live outside the repo and are passed in as files.

  python3 tools/edv.py newkey                          -> prints a new random data key (base64)
  python3 tools/edv.py users  KEYFILE USERS.json       -> writes keys.json  (who may unlock)
  python3 tools/edv.py lock   KEYFILE plain.json out.enc.json   -> encrypts one data file

USERS.json = [{"id": "umar", "password": "..."}, ...]   (keep it OUT of the repo)
KEYFILE    = a file holding the base64 data key           (keep it OUT of the repo)

Crypto: AES-256-GCM for the data. Each user gets the data key wrapped with
AES-256-GCM under PBKDF2-SHA256 (310000 rounds, 16-byte random salt) of
"<id lower-case>:<password>". User entries are stored under SHA-256(id) so
IDs are not readable in the repo. Matches the WebCrypto code in index.html.
"""
import base64, hashlib, json, os, sys, datetime

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover
    os.system(f"{sys.executable} -m pip install -q --break-system-packages cryptography")
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROUNDS = 310000
b64 = lambda b: base64.b64encode(b).decode()
ub64 = lambda s: base64.b64decode(s)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_key(path):
    k = ub64(open(path).read().strip())
    assert len(k) == 32, "data key must be 32 bytes"
    return k


def cmd_newkey():
    print(b64(os.urandom(32)))


def cmd_users(keyfile, usersfile):
    k = read_key(keyfile)
    users = json.load(open(usersfile))
    out = {"v": 1, "rounds": ROUNDS, "users": {}}
    for u in users:
        uid = u["id"].strip().lower()
        salt, iv = os.urandom(16), os.urandom(12)
        kek = hashlib.pbkdf2_hmac("sha256", f"{uid}:{u['password']}".encode(), salt, ROUNDS, 32)
        out["users"][hashlib.sha256(uid.encode()).hexdigest()] = {
            "s": b64(salt), "i": b64(iv), "w": b64(AESGCM(kek).encrypt(iv, k, b"edvertico-key"))}
    json.dump(out, open(os.path.join(ROOT, "keys.json"), "w"), indent=0)
    print("keys.json:", len(out["users"]), "users")


def cmd_lock(keyfile, plain, out):
    k = read_key(keyfile)
    data = open(plain, "rb").read()
    json.loads(data)  # must be valid JSON
    iv = os.urandom(12)
    env = {"v": 1, "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "iv": b64(iv), "ct": b64(AESGCM(k).encrypt(iv, data, b"edvertico-data"))}
    json.dump(env, open(out, "w"))
    print(out, len(data), "bytes locked")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    {"newkey": cmd_newkey, "users": cmd_users, "lock": cmd_lock}[a[0]](*a[1:])
