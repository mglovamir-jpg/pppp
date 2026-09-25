#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.client, json, signal, ssl, sys, threading, time, urllib.parse

HOST = "api.vk.com"
PATH = "/method/groups.edit"
V    = "5.192"
CONC = 96


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


class Conn:
    __slots__ = ("c",)

    def __init__(self):
        self.c = http.client.HTTPSConnection(HOST, 443, timeout=6.0, context=_ctx)
        self.c.connect()

    def post(self, body):
        for _ in (0, 1):
            try:
                self.c.request(
                    "POST", PATH, body,
                    {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0",
                        "Connection": "keep-alive",
                    },
                )
                r = self.c.getresponse()
                return r.read()
            except Exception:
                try:
                    self.c.close()
                except Exception:
                    pass
                try:
                    self.c = http.client.HTTPSConnection(
                        HOST, 443, timeout=6.0, context=_ctx
                    )
                    self.c.connect()
                except Exception:
                    pass
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
    state = {"n": 0, "t0": time.monotonic(), "ok": False}

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: stop.set())
        except Exception:
            pass

    pre = []
    for _ in range(CONC):
        try:
            pre.append(Conn())
        except Exception:
            pre.append(None)

    def worker(conn):
        local_n = 0
        if conn is None:
            try:
                conn = Conn()
            except Exception:
                return
        while not stop.is_set():
            data = conn.post(body)
            local_n += 1
            if local_n >= 8:
                with lock:
                    state["n"] += local_n
                local_n = 0

            if data is None:
                continue
            try:
                d = json.loads(data)
            except Exception:
                continue

            if "response" in d:
                with lock:
                    state["n"] += local_n
                    state["ok"] = True
                    n = state["n"]
                print(f"\n[+] успех #{n}: {d['response']}")
                print(f"[+] https://vk.com/{name}")
                stop.set()
                return

        with lock:
            state["n"] += local_n

    def report():
        prev = 0
        while not stop.is_set():
            time.sleep(1.0)
            n = state["n"]
            dt = time.monotonic() - state["t0"]
            print(f"\r[*] {n} | {n-prev}/s | {dt:.0f}s",
                  end="", flush=True)
            prev = n

    threads = [threading.Thread(target=worker, args=(c,), daemon=True)
               for c in pre]
    rt = threading.Thread(target=report, daemon=True)

    print(f"[*] {CONC} потоков")
    for t in threads:
        t.start()
    rt.start()

    try:
        while not stop.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        stop.set()

    stop.set()
    time.sleep(0.2)
    dt = time.monotonic() - state["t0"]
    print(f"\n[*] {state['n']} за {dt:.1f}s")


if __name__ == "__main__":
    main()
