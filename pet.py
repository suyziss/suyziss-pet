#!/usr/bin/env python3
"""Suyziss Pet: a customizable offline virtual pet for Termux."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SAVE_FILE = DATA_DIR / "pet.json"

TEXT = {
    "ru": {
        "welcome": "Добро пожаловать в SUYZISS PET",
        "subtitle": "Твой маленький питомец живёт прямо в Termux.",
        "hunger": "Сытость", "energy": "Энергия", "happy": "Настроение",
        "xp": "Опыт", "coins": "Монеты", "snacks": "Вкусняшки",
        "menu": ["Покормить", "Поиграть", "Поспать", "Погладить", "Профиль", "Настройки", "Сохранить", "Выйти"],
        "choose": "Выбери действие", "snack": "Питомец с удовольствием съел вкусняшку.",
        "bought": "Ты купил еду за 5 монет.", "no_food": "Нет еды и монет. Поиграй, чтобы заработать.",
        "tired": "Питомец устал. Дай ему отдохнуть.",
        "played": "Вы отлично провели время! +3 монеты.", "slept": "Питомец хорошо отдохнул.",
        "petted": "Ты аккуратно погладил питомца.", "saved": "Игра сохранена.",
        "bye": "До встречи! Прогресс сохранён.", "unknown": "Неизвестная команда.",
        "level": "Новый уровень", "profile": "ПРОФИЛЬ", "created": "Создан",
        "actions": "Действий", "settings": "НАСТРОЙКИ", "name": "Имя",
        "species": "Вид питомца", "language": "Язык", "color": "Цветной интерфейс",
        "on": "Вкл", "off": "Выкл", "change_name": "Изменить имя",
        "change_species": "Изменить вид", "change_language": "Изменить язык",
        "toggle_color": "Переключить цвет", "back": "Назад", "new_name": "Введи новое имя",
        "species_prompt": "Выбери вид: 1) Кот  2) Пёс  3) Кролик",
        "language_prompt": "Выбери язык: 1) Русский  2) English",
        "changed": "Настройка обновлена.", "invalid": "Неверный выбор.",
        "species_names": {"cat": "кот", "dog": "пёс", "rabbit": "кролик"},
        "press": "Нажми Enter, чтобы продолжить..."
    },
    "en": {
        "welcome": "Welcome to SUYZISS PET",
        "subtitle": "Your little companion lives right in Termux.",
        "hunger": "Hunger", "energy": "Energy", "happy": "Happiness",
        "xp": "XP", "coins": "Coins", "snacks": "Snacks",
        "menu": ["Feed", "Play", "Sleep", "Pet", "Profile", "Settings", "Save", "Exit"],
        "choose": "Choose an action", "snack": "Your pet enjoyed a snack.",
        "bought": "You bought food for 5 coins.", "no_food": "No food or coins. Play to earn some.",
        "tired": "Your pet is tired. Let it rest.",
        "played": "You had fun together! +3 coins.", "slept": "Your pet had a nice rest.",
        "petted": "You gently petted your pet.", "saved": "Game saved.",
        "bye": "See you soon! Progress saved.", "unknown": "Unknown command.",
        "level": "Level up", "profile": "PROFILE", "created": "Created",
        "actions": "Actions", "settings": "SETTINGS", "name": "Name",
        "species": "Pet type", "language": "Language", "color": "Colored interface",
        "on": "On", "off": "Off", "change_name": "Change name",
        "change_species": "Change pet type", "change_language": "Change language",
        "toggle_color": "Toggle colors", "back": "Back", "new_name": "Enter a new name",
        "species_prompt": "Choose type: 1) Cat  2) Dog  3) Rabbit",
        "language_prompt": "Choose language: 1) Русский  2) English",
        "changed": "Setting updated.", "invalid": "Invalid choice.",
        "species_names": {"cat": "cat", "dog": "dog", "rabbit": "rabbit"},
        "press": "Press Enter to continue..."
    }
}

DEFAULT_SAVE = {
    "name": "Suyziss", "species": "cat", "language": "ru", "colors": True,
    "created_at": int(time.time()), "last_seen": int(time.time()),
    "hunger": 82, "energy": 90, "happiness": 85, "level": 1, "xp": 0,
    "coins": 20, "inventory": {"snack": 3}, "total_actions": 0
}

ART = {
    "cat": " /\\_/\\\n( o.o )\n > ^ <",
    "dog": " /\\__\\\n(  o.o )\n /    \\",
    "rabbit": " (\\_/ )\n ( o.o )\n / >🍀"
}
RESET = "\033[0m"
ACCENT = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"


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
        if save.get("language") not in TEXT:
            save["language"] = "ru"
        if save.get("species") not in ART:
            save["species"] = "cat"
        now = int(time.time())
        elapsed = max(0, min(now - int(save.get("last_seen", now)), 7 * 86400))
        hours = elapsed // 3600
        save["hunger"] = clamp(save["hunger"] - hours * 2)
        save["energy"] = clamp(save["energy"] + hours)
        save["happiness"] = clamp(save["happiness"] - hours)
        save["last_seen"] = now
        return save
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        try:
            SAVE_FILE.replace(SAVE_FILE.with_suffix(".broken.json"))
        except OSError:
            pass
        print("Save file is damaged; a new save will be created.")
        save = DEFAULT_SAVE.copy()
        save["inventory"] = DEFAULT_SAVE["inventory"].copy()
        return save


def write_save(save: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save["last_seen"] = int(time.time())
    temp = SAVE_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(save, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temp.replace(SAVE_FILE)


def tr(save: dict) -> dict:
    return TEXT.get(save.get("language", "ru"), TEXT["ru"])


def paint(save: dict, value: str, color: str) -> str:
    return f"{color}{value}{RESET}" if save.get("colors", True) else value


def bar(value: int, save: dict) -> str:
    value = clamp(value)
    filled = round(value / 10)
    return paint(save, "[" + "#" * filled + "-" * (10 - filled) + f"] {value:3d}/100", GREEN if value >= 50 else YELLOW)


def pet_art(save: dict) -> str:
    return ART.get(save.get("species", "cat"), ART["cat"])


def show_status(save: dict) -> None:
    t = tr(save)
    print("\n" + paint(save, pet_art(save), ACCENT))
    species = t["species_names"].get(save["species"], save["species"])
    print(paint(save, f"  {save['name']} ({species})  |  Level {save['level']}", ACCENT))
    print("-" * 43)
    print(f"{t['hunger']:<12}: {bar(save['hunger'], save)}")
    print(f"{t['energy']:<12}: {bar(save['energy'], save)}")
    print(f"{t['happy']:<12}: {bar(save['happiness'], save)}")
    print(f"{t['xp']}: {save['xp']}/100     {t['coins']}: {save['coins']}")
    print(f"{t['snacks']}: {save['inventory'].get('snack', 0)}")
    print("-" * 43)


def gain_xp(save: dict, amount: int) -> None:
    save["xp"] += amount
    while save["xp"] >= 100:
        save["xp"] -= 100
        save["level"] += 1
        save["coins"] += 10
        print(f"{tr(save)['level']}! {save['name']} — {save['level']} (+10 {tr(save)['coins'].lower()}).")


def settings(save: dict) -> None:
    while True:
        t = tr(save)
        print("\n" + paint(save, t["settings"], ACCENT))
        print(f"1) {t['change_name']}: {save['name']}")
        print(f"2) {t['change_species']}: {t['species_names'][save['species']]}")
        print(f"3) {t['change_language']}: {save['language']}")
        print(f"4) {t['toggle_color']}: {t['on'] if save['colors'] else t['off']}")
        print(f"0) {t['back']}")
        choice = input("> ").strip()
        if choice == "1":
            name = input(t["new_name"] + ": ").strip()[:20]
            if name:
                save["name"] = name
                print(t["changed"])
        elif choice == "2":
            print(t["species_prompt"])
            species = {"1": "cat", "2": "dog", "3": "rabbit"}.get(input("> ").strip())
            if species:
                save["species"] = species
                print(t["changed"])
            else:
                print(t["invalid"])
        elif choice == "3":
            print(t["language_prompt"])
            lang = {"1": "ru", "2": "en"}.get(input("> ").strip())
            if lang:
                save["language"] = lang
                print(tr(save)["changed"])
            else:
                print(t["invalid"])
        elif choice == "4":
            save["colors"] = not save["colors"]
            print(tr(save)["changed"])
        elif choice == "0":
            write_save(save)
            return
        else:
            print(t["invalid"])
        write_save(save)


def action(save: dict, choice: str) -> bool:
    t = tr(save)
    if choice == "1":
        if save["inventory"].get("snack", 0) > 0:
            save["inventory"]["snack"] -= 1
            save["hunger"] = clamp(save["hunger"] + 22)
            save["happiness"] = clamp(save["happiness"] + 4)
            gain_xp(save, 8)
            print(t["snack"])
        elif save["coins"] >= 5:
            save["coins"] -= 5
            save["hunger"] = clamp(save["hunger"] + 18)
            gain_xp(save, 5)
            print(t["bought"])
        else:
            print(t["no_food"])
    elif choice == "2":
        if save["energy"] < 12:
            print(t["tired"])
            return True
        save["energy"] = clamp(save["energy"] - 12)
        save["hunger"] = clamp(save["hunger"] - 7)
        save["happiness"] = clamp(save["happiness"] + 18)
        save["coins"] += 3
        gain_xp(save, 15)
        print(t["played"])
    elif choice == "3":
        save["energy"] = clamp(save["energy"] + 35)
        save["hunger"] = clamp(save["hunger"] - 3)
        gain_xp(save, 3)
        print(t["slept"])
    elif choice == "4":
        save["happiness"] = clamp(save["happiness"] + 8)
        gain_xp(save, 4)
        print(t["petted"])
    elif choice == "5":
        print(f"\n{t['profile']}: {save['name']}")
        print(f"{t['species']}: {t['species_names'][save['species']]}")
        print(f"{t['created']}: {time.strftime('%Y-%m-%d', time.localtime(save['created_at']))}")
        print(f"{t['actions']}: {save['total_actions']}")
        print(f"{t['coins']}: {save['coins']}")
        input(t["press"])
        return True
    elif choice == "6":
        settings(save)
        return True
    elif choice == "7":
        write_save(save)
        print(t["saved"])
        return True
    elif choice == "0":
        write_save(save)
        print(t["bye"])
        return False
    else:
        print(t["unknown"])
        return True
    save["total_actions"] += 1
    write_save(save)
    return True


def main() -> None:
    save = load_save()
    t = tr(save)
    print(paint(save, t["welcome"], ACCENT))
    print(t["subtitle"])
    while True:
        show_status(save)
        t = tr(save)
        for index, label in enumerate(t["menu"]):
            print(f"{index + 1 if index < 7 else 0}) {label}")
        try:
            choice = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + t["bye"])
            write_save(save)
            break
        if not action(save, choice):
            break


if __name__ == "__main__":
    main()
