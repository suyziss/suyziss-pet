# Suyziss Pet

A customizable offline virtual pet for Termux, written in Python. Your progress is saved locally on your device.

## Features

- Russian and English interface (Russian is the default).
- Customize your pet's name and choose a cat, dog, or rabbit.
- Toggle colored terminal interface.
- Feed, play, rest, and pet your companion.
- Hunger, energy, happiness, level, XP, coins, and snacks.
- Local save in `data/pet.json`; no internet connection or extra Python packages are required.

## Install on Termux

```bash
pkg update
pkg install python git
git clone https://github.com/suyziss/suyziss-pet.git
cd suyziss-pet
python pet.py
```

## Settings

Open **Settings** in the game menu to:
1. Change your pet's name.
2. Choose its type: cat, dog, or rabbit.
3. Switch between Russian and English.
4. Enable or disable terminal colors.

Settings and game progress are stored in `data/pet.json`.

## Backup your progress manually

Cloud synchronization is currently disabled. To keep a backup, copy the local save file:

```bash
cp data/pet.json data/pet-backup.json
```

To restore it, copy the backup over the save file:

```bash
cp data/pet-backup.json data/pet.json
```

Keep backup files private if they contain personal customizations.

## Project layout

```
pet.py                 Offline virtual pet game
data/pet.json          Local save (created automatically)
```

Made by [@suyziss](https://github.com/suyziss).
