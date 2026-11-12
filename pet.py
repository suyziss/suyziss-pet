#!/usr/bin/env python3
"""Suyziss Pet: a lightweight virtual pet for Termux."""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SAVE_FILE = DATA_DIR / "pet.json"

DEFAULT_SAVE = {
    "name": "Suyziss",
    "species": "cat",
    "created_at": int(time.time()),
    "last_seen": int(time.time()),
    "hunger": 82,
    "energy": 90,
    "happiness": 85,
    "level": 1,
    "xp": 0,
    "coins": 20,
    "inventory": {"snack": 3},
    "total_actions": 0,
}


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(value)))


def load_save() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SAVE_FILE.exists():
        save = DEFAULT_SAVE.copy()
        save["inventory"] = DEFAULT_SAVE["inventory"].copy()
        write_save(save)
        return save
    try:
        with SAVE_FILE.open("r", encoding="utf-8") as handle:
            save = json.load(handle)
        for key, value in DEFAULT_SAVE.items():
            save.setdefault(key, value.copy() if isinstance(value, dict) else value)
        now = int(time.time())
        elapsed = max(0, min(now - int(save.get("last_seen", now)), 7 * 24 * 3600))
        # Gentle offline decay, capped to one week.
        hours = elapsed // 3600
        save["hunger"] = clamp(save["hunger"] - hours * 2)
        save["energy"] = clamp(save["energy"] + hours)
        save["happiness"] = clamp(save["happiness"] - hours)
        save["last_seen"] = now
        return save
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        backup = SAVE_FILE.with_suffix(".broken.json")
        try:
            SAVE_FILE.replace(backup)
        except OSError:
            pass
        print("Save file could not be read. A fresh save will be created.")
        return DEFAULT_SAVE.copy()


def write_save(save: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save["last_seen"] = int(time.time())
    temp = SAVE_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(save, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temp.replace(SAVE_FILE)


def bar(value: int) -> str:
    filled = round(clamp(value) / 10)
    return "[" + "#" * filled + "-" * (10 - filled) + f"] {clamp(value):3d}/100"


def pet_art(mood: int) -> str:
    face = "o.o" if mood >= 35 else "u.u"
    return f"      /\\_/\\\n     ( {face} )\n      > ^ <"


def show_status(save: dict) -> None:
    print("\n" + pet_art(save["happiness"]))
    print(f"             {save['name']}  |  Level {save['level']}")
    print("-" * 39)
    print(f"Hunger:    {bar(save['hunger'])}")
    print(f"Energy:    {bar(save['energy'])}")
    print(f"Happiness: {bar(save['happiness'])}")
    print(f"XP: {save['xp']}/100     Coins: {save['coins']}")
    print(f"Snacks: {save['inventory'].get('snack', 0)}")
    print("-" * 39)


def gain_xp(save: dict, amount: int) -> None:
    save["xp"] += amount
    while save["xp"] >= 100:
        save["xp"] -= 100
        save["level"] += 1
        save["coins"] += 10
        print(f"\nLevel up! {save['name']} reached level {save['level']} (+10 coins).")


def action(save: dict, choice: str) -> None:
    if choice == "1":
        if save["inventory"].get("snack", 0) > 0:
            save["inventory"]["snack"] -= 1
            save["hunger"] = clamp(save["hunger"] + 22)
            save["happiness"] = clamp(save["happiness"] + 4)
            gain_xp(save, 8)
            print(f"{save['name']} enjoyed a snack.")
        elif save["coins"] >= 5:
            save["coins"] -= 5
            save["hunger"] = clamp(save["hunger"] + 18)
            gain_xp(save, 5)
            print("You bought a snack for 5 coins.")
        else:
            print("No snacks or coins. Play a little to earn coins.")
    elif choice == "2":
        if save["energy"] < 12:
            print(f"{save['name']} is too tired to play. Let them rest.")
            return
        save["energy"] = clamp(save["energy"] - 12)
        save["hunger"] = clamp(save["hunger"] - 7)
        save["happiness"] = clamp(save["happiness"] + 18)
        save["coins"] += 3
        gain_xp(save, 15)
        print(f"{save['name']} had fun! +3 coins.")
    elif choice == "3":
        save["energy"] = clamp(save["energy"] + 35)
        save["hunger"] = clamp(save["hunger"] - 3)
        print(f"{save['name']} had a nice rest.")
        gain_xp(save, 3)
    elif choice == "4":
        save["happiness"] = clamp(save["happiness"] + 8)
        gain_xp(save, 4)
        print(f"You gently petted {save['name']}.")
    elif choice == "5":
        print(f"\n{save['name']} is a level {save['level']} {save['species']}.")
        print(f"Created: {time.strftime('%Y-%m-%d', time.localtime(save['created_at']))}")
        print(f"Actions taken: {save['total_actions']}")
        print(f"Coins: {save['coins']}")
        return
    elif choice == "6":
        write_save(save)
        print("Local save written.")
        return
    elif choice == "0":
        write_save(save)
        print("See you soon. Your pet is saved.")
        raise SystemExit(0)
    else:
        print("Unknown option.")
        return
    save["total_actions"] += 1
    write_save(save)


def main() -> None:
    save = load_save()
    print("Welcome to SUYZISS PET")
    print("Your little companion lives right in Termux.")
    while True:
        show_status(save)
        print("1) Feed   2) Play   3) Sleep")
        print("4) Pet    5) Profile  6) Save")
        print("0) Exit")
        try:
            choice = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaving...")
            write_save(save)
            break
        action(save, choice)


if __name__ == "__main__":
    main()
