#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Захват адреса (screen_name) группы ВК через пользовательский токен.
Требуется 2FA на аккаунте и права администратора/владельца группы.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.vk.com/method/"
API_VERSION = "5.192"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ---------------------------------------------------------------------------
# HTTP без прокси (ключ привязан к IP)
# ---------------------------------------------------------------------------

def api_call(method: str, params: dict) -> dict:
    params = dict(params)
    params["v"] = API_VERSION
    url = API + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "vk-domain-taker/1.0"})
    # Намеренно без ProxyHandler — VK-ключ привязан к IP выдачи.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=20) as r:
            data = r.read().decode("utf-8", "replace")
    except Exception as e:
        return {"_transport_error": str(e)}
    try:
        return json.loads(data)
    except Exception:
        return {"_parse_error": data[:500]}


# ---------------------------------------------------------------------------
# Конфиг
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] config.json не прочитан: {e}")
    return {}


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Хелперы ввода
# ---------------------------------------------------------------------------

def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default and not secret else ""
    if secret and default:
        suffix = " [из config.json]"
    try:
        val = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[выход]")
        sys.exit(1)
    if not val and default:
        return default
    return val


def normalize_group_id(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("-"):
        raw = raw[1:]
    if raw.startswith("club"):
        raw = raw[4:]
    if raw.startswith("public"):
        raw = raw[6:]
    if not raw.isdigit():
        print(f"[!] '{raw}' не похоже на числовой id группы")
        sys.exit(2)
    return raw


def normalize_screen_name(raw: str) -> str:
    raw = raw.strip().lower()
    for prefix in ("https://vk.com/", "http://vk.com/", "vk.com/", "@"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    raw = raw.strip("/")
    return raw


# ---------------------------------------------------------------------------
# Проверки
# ---------------------------------------------------------------------------

def check_token(token: str) -> dict | None:
    r = api_call("users.get", {"access_token": token})
    if "_transport_error" in r or "_parse_error" in r:
        print(f"[!] Сеть/парсинг: {r}")
        return None
    if "error" in r:
        print_error(r["error"])
        return None
    if not r.get("response"):
        print("[!] users.get вернул пустой ответ")
        return None
    me = r["response"][0]
    print(f"[+] Токен живой. Аккаунт: {me.get('first_name')} {me.get('last_name')} (id {me.get('id')})")
    return me


def check_group(token: str, gid: str) -> dict | None:
    r = api_call("groups.getById", {
        "access_token": token,
        "group_id": gid,
        "fields": "screen_name,is_admin,admin_level,can_manage",
    })
    if "_transport_error" in r or "_parse_error" in r:
        print(f"[!] Сеть/парсинг: {r}")
        return None
    if "error" in r:
        print_error(r["error"])
        return None
    groups = r.get("response", {}).get("groups") or r.get("response") or []
    if not groups:
        print("[!] Группа не найдена")
        return None
    g = groups[0]
    print(f"[+] Группа: {g.get('name')} (id {g.get('id')})")
    print(f"    текущий адрес: vk.com/{g.get('screen_name') or '—'}")
    print(f"    is_admin={g.get('is_admin')} admin_level={g.get('admin_level')} can_manage={g.get('can_manage')}")
    if not (g.get("is_admin") or g.get("admin_level", 0) >= 3):
        print("[!] Аккаунт НЕ админ/владелец — адрес поменять не получится")
        return None
    return g


# ---------------------------------------------------------------------------
# Основное действие
# ---------------------------------------------------------------------------

def try_set_screen_name(token: str, gid: str, name: str, password: str = "") -> bool:
    params = {
        "access_token": token,
        "group_id": gid,
        "screen_name": name,
    }
    if password:
        params["password"] = password

    print(f"\n[*] groups.edit: group_id={gid} screen_name={name}")
    r = api_call("groups.edit", params)

    if "_transport_error" in r or "_parse_error" in r:
        print(f"[!] Сеть/парсинг: {r}")
        return False

    if "error" in r:
        err = r["error"]
        code = err.get("error_code")
        msg = err.get("error_msg", "")

        # 14 — капча
        if code == 14:
            cap = err.get("captcha_img") or (err.get("captcha") or {}).get("img")
            sid = err.get("captcha_sid") or (err.get("captcha") or {}).get("sid")
            print(f"[!] Капча. Открой картинку, введи текст вручную.")
            print(f"    captcha_img: {cap}")
            print(f"    captcha_sid: {sid}")
            key = input("    captcha_key: ").strip()
            if key:
                params["captcha_sid"] = sid
                params["captcha_key"] = key
                r2 = api_call("groups.edit", params)
                if "error" in r2:
                    print_error(r2["error"])
                    return False
                print("[+] Ответ VK:", r2)
                return True
            return False

        # 17 — требуется пароль
        if code == 17:
            print("[!] VK требует подтверждение паролем (error 17)")
            pwd = input("    пароль аккаунта: ").strip()
            if pwd:
                return try_set_screen_name(token, gid, name, password=pwd)
            return False

        print_error(err)
        return False

    print("[+] Ответ VK:", r)
    return True


def print_error(err: dict) -> None:
    code = err.get("error_code")
    msg = err.get("error_msg", "")
    hints = {
        5:   "ключ мёртв / отозван / запрос с другого IP",
        6:   "флуд — снизь частоту запросов",
        14:  "нужна капча",
        15:  "нет прав или не тот тип ключа",
        17:  "требуется подтверждение паролем",
        27:  "метод недоступен с группового ключа (нужен user token)",
        100: "адрес занят ЛИБО параметр некорректен (на занятом адресе VK отдаёт именно 100)",
        203: "доступ к сообществу запрещён — клуб не в управлении",
        1260:"Invalid screen name (адрес занят или недопустим)",
    }
    hint = hints.get(code, "")
    print(f"[!] VK error {code}: {msg}")
    if hint:
        print(f"    → {hint}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print(" ЗАХВАТ АДРЕСА ГРУППЫ ВК")
    print("=" * 60)

    cfg = load_config()

    token = ask("Токен (vk1.a....)", cfg.get("token", ""), secret=True)
    if not token:
        print("[!] Токен обязателен")
        sys.exit(2)

    if not check_token(token):
        sys.exit(3)

    raw_gid = ask("ID группы (числом, можно с - или club)", cfg.get("group_id", ""))
    if not raw_gid:
        print("[!] ID группы обязателен")
        sys.exit(2)
    gid = normalize_group_id(raw_gid)

    if not check_group(token, gid):
        sys.exit(4)

    raw_name = ask("Желаемый адрес (screen_name)", cfg.get("target_name", ""))
    if not raw_name:
        print("[!] Адрес обязателен")
        sys.exit(2)
    name = normalize_screen_name(raw_name)
    print(f"[*] Целевой адрес: vk.com/{name}")

    ok = try_set_screen_name(token, gid, name)

    # Сохраняем то, что вводили (кроме пароля)
    cfg.update({
        "token": token,
        "group_id": gid,
        "target_name": name,
        "vk_proxy": "direct",
        "rps": cfg.get("rps", 3),
    })
    save_config(cfg)
    print(f"[*] config.json обновлён: {CONFIG_PATH}")

    if ok:
        print("\n[+] ГОТОВО. Проверь: https://vk.com/" + name)
    else:
        print("\n[!] Не удалось. Смотри ошибку выше.")


if __name__ == "__main__":
    main()
