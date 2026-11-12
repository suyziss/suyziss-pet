# Suyziss Pet

A small virtual pet for Termux, written in Python. Your pet's progress is stored locally and can be backed up to GitHub, then restored on another Android device.

## Features

- Feed, play with, rest, and care for your pet.
- Hunger, energy, happiness, level, XP, coins, and inventory.
- State persists locally in `data/pet.json`.
- GitHub cloud backup and restore.
- Cloud save is encrypted locally with a passphrase before upload. The public repository only receives ciphertext.
- Conflict checks help prevent accidental overwrites between devices.

## Requirements

- Termux (install from F-Droid or the official Termux GitHub releases).
- Python 3.10+.
- A GitHub account and a fine-grained personal access token with **Contents: Read and write** permission for this repository.

## Install on Termux

```bash
pkg update
pkg install python git
git clone https://github.com/suyziss/suyziss-pet.git
cd suyziss-pet
python -m pip install -r requirements.txt
python pet.py
```

## Set up GitHub sync

1. On GitHub, create a fine-grained personal access token. Restrict it to this repository and grant **Contents: Read and write**. Do not share the token.
2. Run:

```bash
python sync.py setup
```

3. Enter the token when prompted. It is stored in your Termux home config directory with owner-only permissions.
4. Choose a strong backup passphrase when prompted by the first push or pull. **The passphrase is not uploaded or stored by this app. Keep it safe.**

Back up your pet:

```bash
python sync.py push
```

Restore on another device:

```bash
pkg update
pkg install python git
git clone https://github.com/suyziss/suyziss-pet.git
cd suyziss-pet
python -m pip install -r requirements.txt
python sync.py setup
python sync.py pull
python pet.py
```

Use the same GitHub token permissions and the same backup passphrase on each device. The restore command asks before replacing an existing local save.

## Commands

Start the pet with `python pet.py`. In the menu you can feed, play, rest, inspect stats, and save.

Cloud commands:

- `python sync.py setup` — securely save your GitHub token locally.
- `python sync.py push` — encrypt and upload the local save.
- `python sync.py pull` — download, decrypt, and restore the cloud save.
- `python sync.py status` — check whether a cloud save exists.

## Important backup notes

- This is a backup/restore workflow, not automatic real-time synchronization. Before switching devices, push on the old device and pull on the new one.
- Do not push from two devices with diverging progress. Pull the latest save first. The tool refuses to overwrite a cloud version it has not previously seen.
- If you lose the passphrase, the encrypted backup cannot be recovered.
- The repository is public. The encrypted save is safe to publish only while your passphrase remains private and strong. Never upload your GitHub token, passphrase, or an unencrypted save.
- GitHub is a third-party service; keep an additional offline backup if the pet's progress is important.

## Project layout

```
pet.py                 Virtual pet game
sync.py                GitHub encrypted backup/restore
requirements.txt       Python dependencies
data/                  Local save (created automatically; git-ignored)
```

Made by [@suyziss](https://github.com/suyziss).
