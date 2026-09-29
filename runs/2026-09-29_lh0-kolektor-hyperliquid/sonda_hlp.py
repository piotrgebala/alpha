"""LH0 krok 0a(i): kto w HLP wykonuje likwidacje? Tylko publiczne Info API, bez klucza, bez zapisu poza stdout.

Kroki:
1. `vaultDetails` dla adresu HLP podanego w dokumentacji Info API (przykład odpowiedzi `vaultDetails`,
   opis „performs liquidations”) -> nazwa, opis, adresy podrzędne (`relationship.childAddresses`).
2. Dla HLP i każdego adresu podrzędnego: `userFills` (ostatnie wypełnienia, do 2000) -> ile ma pole
   `liquidation`, z jaką metodą (`market` / `backstop`) i w jakim przedziale czasu.

Uruchomienie: python runs/2026-09-29_lh0-kolektor-hyperliquid/sonda_hlp.py
"""

import collections
import datetime as dt
import json
import time
import urllib.request

INFO_URL = "https://api.hyperliquid.xyz/info"
# Adres z dokumentacji Info API (przykład `vaultDetails`, opis: "... performs liquidations ...").
HLP_DOC = "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"


def info(body):
    req = urllib.request.Request(
        INFO_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read(20_000_000))


def utc(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main():
    print("czas sondy UTC:", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    vd = info({"type": "vaultDetails", "vaultAddress": HLP_DOC})
    print("vaultDetails: name =", vd.get("name"), "| leader =", vd.get("leader"))
    print("description =", vd.get("description"))
    rel = vd.get("relationship") or {}
    children = (rel.get("data") or {}).get("childAddresses", [])
    print("relationship.type =", rel.get("type"), "| childAddresses =", children)
    for addr in [HLP_DOC] + children:
        time.sleep(1)
        fills = info({"type": "userFills", "user": addr})
        liq = [f for f in fills if f.get("liquidation")]
        methods = collections.Counter(f["liquidation"].get("method") for f in liq)
        span = (
            f"{utc(min(f['time'] for f in fills))} .. {utc(max(f['time'] for f in fills))}"
            if fills
            else "-"
        )
        print(
            f"\n{addr}: fills={len(fills)} okno={span} z polem liquidation={len(liq)} metody={dict(methods)}"
        )
        for f in liq[:3]:
            print("  przyklad:", json.dumps(f)[:400])
        # jak się podpisuje strona likwidowanego w wypełnieniu kontrahenta
        lu = collections.Counter(bool(f["liquidation"].get("liquidatedUser")) for f in liq)
        print("  liquidatedUser obecny:", dict(lu))


if __name__ == "__main__":
    main()
