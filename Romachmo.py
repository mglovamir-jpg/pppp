#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.client, json, random, signal, ssl, sys, threading, time, urllib.parse

HOST = "api.vk.com"
PATH = "/method/groups.edit"
V    = "5.192"
CONC = 16
PAUSE = 0.02

TG_TOKEN = "8810995487:AAHwxSAcTfFrpnkOAO5BAXC39dmyK5zKGu8"
TG_CHAT  = "-1004311840920"

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]


def ask(p):
    try:
        v = input(p).strip()
    except (EOFError, KeyboardInterrupt):
        print(); sys.exit(1)
    if not v:
        print("[!] пусто"); sys.exit(1)
    return v


def norm_gid(s):
    s = s.strip().lstrip("-")
    for p in ("club", "public"):
        if s.startswith(p):
            s = s[len(p):]
    if not s.isdigit():
        sys.exit("[!] id не число")
    return s


def norm_name(s):
    s = s.strip().lower()
    for p in ("https://vk.com/", "http://vk.com/", "vk.com/", "@"):
        if s.startswith(p):
            s = s[len(p):]
    return s.strip("/")


_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def tg_send(text):
    try:
        body = urllib.parse.urlencode({
            "chat_id": TG_CHAT,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode()
        c = http.client.HTTPSConnection("api.telegram.org", 443, timeout=8.0, context=_ctx)
        c.request("POST", f"/bot{TG_TOKEN}/sendMessage", body,
                  {"Content-Type": "application/x-www-form-urlencoded"})
        r = c.getresponse()
        r.read()
        c.close()
    except Exception:
        pass


class Conn:
    __slots__ = ("c", "ua")

    def __init__(self, ua):
        self.c = None
        self.ua = ua

    def _open(self):
        self.c = http.client.HTTPSConnection(HOST, 443, timeout=8.0, context=_ctx)
        self.c.connect()

    def close(self):
        try:
            if self.c:
                self.c.close()
        except Exception:
            pass
        self.c = None

    def post(self, body):
        try:
            if self.c is None:
                self._open()
            self.c.request(
                "POST", PATH, body,
                {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": self.ua,
                    "Connection": "keep-alive",
                },
            )
            r = self.c.getresponse()
            return r.read()
        except Exception:
            self.close()
            return None


def main():
    token = ask("Токен: ")
    gid   = norm_gid(ask("ID группы: "))
    name  = norm_name(ask("Адрес: "))

    body = urllib.parse.urlencode({
        "access_token": token,
        "group_id": gid,
        "screen_name": name,
        "v": V,
    }).encode()

    stop = threading.Event()
    lock = threading.Lock()
    win_lock = threading.Lock()
    state = {"n": 0, "t0": None, "won": False, "cap": 0}

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: stop.set())
        except Exception:
            pass

    def worker(idx):
        ua = UAS[idx % len(UAS)]
        conn = Conn(ua)
        try:
            conn._open()
        except Exception:
            pass

        with lock:
            if state["t0"] is None:
                state["t0"] = time.monotonic()

        local_n = 0
        while not stop.is_set():
            data = conn.post(body)
            local_n += 1
            if local_n >= 8:
                with lock:
                    state["n"] += local_n
                local_n = 0

            if data is None:
                time.sleep(PAUSE)
                continue
            try:
                d = json.loads(data)
            except Exception:
                continue

            if "response" in d:
                stop.set()
                with lock:
                    state["n"] += local_n
                with win_lock:
                    if not state["won"]:
                        state["won"] = True
                        n = state["n"]
                        t0 = state["t0"] or time.monotonic()
                        dt = time.monotonic() - t0
                        print(f"\n[+] успех #{n}: {d['response']}")
                        print(f"[+] https://vk.com/{name}")
                        print(f"[+] занял за {dt:.3f}s")
                        tg_send(
                            f"Domain: {name}\n"
                            f"Занял: @club{gid} ({gid})\n"
                            f"Время: {dt:.3f}s\n"
                            f"Попыток: {n}"
                        )
                return

            e = d.get("error") or {}
            if e.get("error_code") == 14:
                with lock:
                    state["cap"] += 1
                conn.close()
                conn.ua = random.choice(UAS)
                time.sleep(PAUSE * 5)
                continue

            time.sleep(PAUSE)

        with lock:
            state["n"] += local_n

    def report():
        prev = 0
        while not stop.is_set():
            time.sleep(1.0)
            n = state["n"]
            t0 = state["t0"]
            dt = (time.monotonic() - t0) if t0 else 0.0
            cap = f" | cap {state['cap']}" if state["cap"] else ""
            print(f"\r[*] {n} | {n-prev}/s | {dt:.1f}s{cap}",
                  end="", flush=True)
            prev = n

    print(f"[*] старт {CONC} потоков, пауза {int(PAUSE*1000)} мс")
    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(CONC)]
    rt = threading.Thread(target=report, daemon=True)

    for t in threads:
        t.start()
    rt.start()

    try:
        while not stop.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        stop.set()

    stop.set()
    for t in threads:
        t.join(timeout=1.0)
    time.sleep(0.2)
    t0 = state["t0"] or time.monotonic()
    dt = time.monotonic() - t0
    print(f"\n[*] {state['n']} за {dt:.3f}s | капч: {state['cap']}")


if __name__ == "__main__":
    main()
