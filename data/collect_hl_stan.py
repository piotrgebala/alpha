"""
collect_hl_stan.py — kolektor stanu rynku Hyperliquid (`metaAndAssetCtxs`, perpetuale głównej giełdy)
co 60 s do plików dziennych `YYYY-MM-DD.jsonl.gz`; działa 24/7 na serwerze obok kolektorów likwidacji
(cron co 5 min przez `tools/likwidacje.sh`, jedna instancja — blokada `flock` w katalogu danych).

Po co (zadanie 010, runda HS0 `runs/2026-10-05_hs0-hl-stan-rynku/`; wniosek 110): Hyperliquid to inna
populacja traderów niż Binance. Stawka fundingu, cena mark/oracle/mid, premia i otwarte pozycje HL na żywo
są bramą danych dla przyszłej karty „funding/premia HL” — ale historii stanu (point-in-time) publiczne API
nie daje, więc zbieramy od dziś. 0 wariantów, 0 odczytów: nic tu nie liczy sygnału ani zwrotu.

Zasady:
- źródło: POST `https://api.hyperliquid.xyz/info` z `{"type": "metaAndAssetCtxs"}` (waga 20; limit IP
  1 200/min — kolektor zużywa 20/min). Adres STAŁY; `sprawdz_adres` odrzuca wszystko poza `https://` na ten
  host; certyfikat i nazwa hosta weryfikowane (`ssl.create_default_context`); przekierowania NIE są
  wykonywane; zmienne `*_proxy` ignorowane; odpowiedź większa niż `MAX_ODP_BYTES` = błąd;
- zapis: pełna odpowiedź + czas wysłania i odbioru (ms UTC) jako jedna linia JSON w ASCII; każda migawka
  to OSOBNY CZŁON gzip dopisany na koniec pliku dnia (dzień UTC czasu odbioru). Standard gzip (RFC 1952)
  dopuszcza wiele członów: `zcat`, `gzip -dc` i `gzip.open` czytają plik jak jeden tekst JSONL;
- awaria traci najwyżej bieżącą migawkę: człon idzie jednym `os.write` + `fsync`; nieudany zapis jest
  cofany (`ftruncate` do rozmiaru sprzed zapisu), a przy pierwszym zapisie do pliku w procesie (start,
  nowy dzień, po błędzie) `napraw_ogon` przycina plik do końca ostatniego pełnego członu — urwany ogon
  po awarii zasilania nie psuje kolejnych migawek;
- odpowiedź sprawdzana przed zapisem (`sprawdz_odpowiedz`: `[meta, konteksty]`, nazwy monet, liczba
  kontekstów = liczba monet; `NaN`/`Infinity` odrzucane już przy parsowaniu); czas odbioru musi spełniać
  wspólną regułę 2019–2100 (`data/liquidation_time.event_time_ms`, zadanie 021) — zegar spoza zakresu
  nie wyprodukuje pliku z absurdalną datą. Zła odpowiedź = brak zapisu + licznik w `status.json`;
- rytm: migawka na każdej pełnej minucie zegara UTC; ponowienia po HTTP 429/5xx, błędach sieci
  i uciętym JSON z rosnącym odczekaniem 2 → 20 s, ale nie dłużej niż do następnej migawki; błąd jednej
  migawki nie przerywa pętli. Plik `WYLACZONY` w katalogu danych zatrzymuje pętlę przed następną migawką
  (cron go wtedy nie wznawia);
- `status.json` (zapis atomowy: plik tymczasowy + `os.replace`, ASCII) po każdej migawce; `--status` dla
  człowieka; `kolektor.log` (start, naprawy pliku, błędy, podsumowanie co godzinę, koniec);
- jedna instancja: `flock` na `<katalog>/.lock`. Pod cronem blokadę bierze powłoka (`tools/likwidacje.sh`,
  deskryptor 7) i przekazuje ją przez `--blokada-fd 7` — kolektor sprawdza, że to ten sam plik i że
  blokada jest jego; uruchomiony ręcznie bierze ją sam. Druga instancja kończy się od razu (kod 0);
- czyste funkcje i pętla z podmienialnymi `post`, `sleep`, `clock`, `wall` — testy bez sieci
  (`tests/test_collect_hl_stan.py`).

Odczyt (analiza, poza kolektorem): `czytaj_dzien(plik)` → lista rekordów; albo `zcat plik | jq`.

    PYTHONUTF8=1 py -m data.collect_hl_stan                       # kolektor (w tle, cron)
    PYTHONUTF8=1 py -m data.collect_hl_stan --status
    PYTHONUTF8=1 py -m data.collect_hl_stan --dir "$(mktemp -d)" --max-cycles 3   # krótka próba
"""

from __future__ import annotations

import datetime as dt
import gzip
import http.client
import json
import math
import os
import signal
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections.abc import Callable
from pathlib import Path

from data import liquidation_time as lt

INFO_URL = "https://api.hyperliquid.xyz/info"
HOST = "api.hyperliquid.xyz"
ZAPYTANIE = {"type": "metaAndAssetCtxs"}
ENV_DIR = "CLAS5_HL_STAN_DIR"
DEFAULT_DIR = Path.home() / "likwidacje_hl" / "stan"
OKRES_S = 60.0
ZAPAS_S = 10.0  # ponowienia kończą się ≥ 10 s przed następną migawką
MAX_ODP_BYTES = 4 * 1024 * 1024  # migawka 2026-09-29: ~72 kB — zapas ~58×
TIMEOUT_S = 20.0
PROBY = 4
BACKOFF_S = 2.0
BACKOFF_MAX_S = 20.0
RETRY_HTTP = (429, 500, 502, 503, 504)
GZIP_POZIOM = 9
KAWAL = 65_536  # odczyt członów przy naprawie ogona (człon ~13,5 kB)
STATUS = "status.json"
WYLACZNIK = "WYLACZONY"
BLOKADA = ".lock"
LOG = "kolektor.log"
PODSUMOWANIE_CO = 60  # wpis w logu co 60 migawek (≈ 1 h)
LOG_PIERWSZE, LOG_CO = 5, 100  # błędy w logu: pierwsze 5, potem co 100.
STARY_STATUS_S = 300.0  # `--status`: ostatnia migawka starsza niż 5 min = uwaga


# ------------------------------------------------------------------ czyste funkcje
def sprawdz_adres(url: str) -> None:
    """Tylko `https://api.hyperliquid.xyz/info` (port domyślny, bez danych logowania) — inaczej ValueError."""
    czesci = urllib.parse.urlsplit(url)
    if (
        czesci.scheme != "https"
        or czesci.hostname != HOST
        or czesci.port not in (None, 443)
        or czesci.username is not None
        or czesci.password is not None
        or czesci.path != "/info"
    ):
        raise ValueError(f"hl stan: dozwolony tylko {INFO_URL}, dostałem {url[:80]!r}")


def _bez_stalych(nazwa: str):
    raise ValueError(f"hl stan: niedozwolona stała JSON {nazwa}")


def parsuj(raw: bytes):
    """Bajty odpowiedzi → JSON; `NaN`/`Infinity` odrzucone (ValueError, jak ucięty JSON)."""
    return json.loads(raw, parse_constant=_bez_stalych)


def sprawdz_odpowiedz(odp) -> int:
    """
    Kształt `metaAndAssetCtxs`: `[meta, konteksty]`, `meta.universe` — niepusta lista rekordów z niepustą
    nazwą (`name`), `konteksty` — lista rekordów tej samej długości. Zwraca liczbę monet; inaczej ValueError.
    """
    if not isinstance(odp, list) or len(odp) != 2:
        raise ValueError("hl stan: odpowiedź nie jest parą [meta, konteksty]")
    meta, konteksty = odp
    if not isinstance(meta, dict) or not isinstance(meta.get("universe"), list):
        raise ValueError("hl stan: brak listy meta.universe")
    monety = meta["universe"]
    if not monety:
        raise ValueError("hl stan: pusta lista monet")
    if not all(
        isinstance(m, dict) and isinstance(m.get("name"), str) and m["name"] for m in monety
    ):
        raise ValueError("hl stan: moneta bez nazwy w meta.universe")
    if not isinstance(konteksty, list) or len(konteksty) != len(monety):
        raise ValueError("hl stan: liczba kontekstów ≠ liczba monet")
    if not all(isinstance(k, dict) for k in konteksty):
        raise ValueError("hl stan: kontekst nie jest rekordem")
    return len(monety)


def czas_utc(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000.0, tz=dt.timezone.utc).isoformat(
        timespec="milliseconds"
    )


def plik_dnia(root: Path, czas_ms: int) -> Path:
    """Plik dnia UTC czasu odbioru; czas łamiący regułę 2019–2100 (zadanie 021) → ValueError."""
    try:
        ms = lt.event_time_ms(czas_ms)
    except ValueError as exc:
        raise ValueError(f"hl stan: czas odbioru {exc}") from None
    dzien = dt.datetime.fromtimestamp(ms / 1000.0, tz=dt.timezone.utc).date()
    return Path(root) / f"{dzien.isoformat()}.jsonl.gz"


def rekord(czas_ms: int, wyslano_ms: int, odp) -> str:
    """Linia JSON (ASCII, bez spacji, zakończona `\\n`): czas odbioru, czas wysłania, pełna odpowiedź."""
    return (
        json.dumps(
            {
                "czas_ms": czas_ms,
                "czas_utc": czas_utc(czas_ms),
                "wyslano_ms": wyslano_ms,
                "odpowiedz": odp,
            },
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def czlon_gzip(dane: bytes) -> bytes:
    """Jeden kompletny człon gzip (nagłówek bez nazwy i bez czasu — deterministyczny)."""
    return gzip.compress(dane, compresslevel=GZIP_POZIOM, mtime=0)


def koniec_pelnych_czlonow(dane: bytes) -> tuple[int, int]:
    """
    (bajt końca ostatniego PEŁNEGO i poprawnego członu gzip od początku `dane`, liczba takich członów).
    Człon urwany, uszkodzony (zła suma CRC, śmieci, zera po awarii) i wszystko za nim — poza wynikiem.
    Czyta kawałkami (`KAWAL`), więc koszt jest liniowy w rozmiarze pliku.
    """
    mv = memoryview(dane)
    poz, n, rozmiar = 0, 0, len(dane)
    while poz < rozmiar:
        d = zlib.decompressobj(wbits=31)  # 16 + 15: format gzip, sprawdza CRC32 i długość
        i = poz
        try:
            while not d.eof and i < rozmiar:
                kawal = mv[i : i + KAWAL]
                d.decompress(kawal)
                i += len(kawal)
        except zlib.error:
            break
        if not d.eof:
            break
        poz = i - len(d.unused_data)
        n += 1
    return poz, n


def napraw_ogon(sciezka: Path) -> tuple[int, int]:
    """Przytnij plik do końca ostatniego pełnego członu. Zwraca (pełnych członów, odciętych bajtów)."""
    sciezka = Path(sciezka)
    if not sciezka.exists():
        return 0, 0
    dane = sciezka.read_bytes()
    koniec, n = koniec_pelnych_czlonow(dane)
    if koniec < len(dane):
        with open(sciezka, "r+b") as f:
            f.truncate(koniec)
            f.flush()
            os.fsync(f.fileno())
    return n, len(dane) - koniec


def czytaj_dzien(sciezka: Path) -> list[dict]:
    """Plik dnia → lista rekordów (wszystkie człony; do analizy, poza kolektorem)."""
    with gzip.open(sciezka, "rt", encoding="ascii") as f:
        return [json.loads(linia) for linia in f if linia.strip()]


def nastepny_termin(teraz_s: float, okres_s: float = OKRES_S) -> float:
    """Najbliższa pełna wielokrotność `okres_s` (czas zegara, s od epoki) ŚCIŚLE po `teraz_s`."""
    return (math.floor(teraz_s / okres_s) + 1) * okres_s


def opoznienie(proba: int, baza: float = BACKOFF_S, sufit: float = BACKOFF_MAX_S) -> float:
    """Odczekanie przed ponowieniem nr `proba` (0, 1, …): 2, 4, 8, … s, sufit 20 s (wykładnik ucięty
    do 30 — duży numer próby nie przepełni liczby zmiennoprzecinkowej)."""
    return float(min(sufit, baza * 2.0 ** min(max(0, proba), 30)))


# ------------------------------------------------------------------ sieć (cienka warstwa)
class _BezPrzekierowan(urllib.request.HTTPRedirectHandler):
    """Przekierowanie NIE jest wykonywane: 3xx kończy się `HTTPError` (adres jest stały)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _opener() -> urllib.request.OpenerDirector:
    """Opener: weryfikacja certyfikatu i nazwy hosta, bez proxy ze zmiennych środowiska, bez przekierowań."""
    ctx = ssl.create_default_context()
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ctx),
        _BezPrzekierowan(),
    )


class ZaDuzaOdpowiedz(ValueError):
    """Odpowiedź większa niż `MAX_ODP_BYTES` (nie ponawiamy — to nie błąd przejściowy)."""


def _post(url: str, body: dict, timeout: float = TIMEOUT_S, limit: int = MAX_ODP_BYTES) -> bytes:
    """POST JSON → surowe bajty odpowiedzi (tylko `INFO_URL`, limit czasu i rozmiaru)."""
    sprawdz_adres(url)
    dane = json.dumps(body, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    req = urllib.request.Request(
        url,
        data=dane,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "alpha-hs0"},
    )
    with _opener().open(req, timeout=timeout) as resp:
        dlugosc = resp.headers.get("Content-Length")
        if dlugosc is not None and dlugosc.isdigit() and int(dlugosc) > limit:
            raise ZaDuzaOdpowiedz(f"hl stan: odpowiedź {dlugosc} B > limit {limit} B")
        raw = resp.read(limit + 1)
    if len(raw) > limit:
        raise ZaDuzaOdpowiedz(f"hl stan: odpowiedź > limit {limit} B")
    return raw


BLEDY_PRZEJSCIOWE = (OSError, http.client.HTTPException, json.JSONDecodeError)


class Klient:
    """
    `metaAndAssetCtxs` z ponowieniami: HTTP 429/5xx, błędy sieci (`OSError`, w tym `URLError`, timeout,
    SSL), zerwana odpowiedź i ucięty JSON → odczekanie `opoznienie(proba)`, najwyżej `proby` prób i nie
    dłużej niż do `termin` (zegar `clock`). Pozostałe 4xx, 3xx, za duża odpowiedź, `NaN` → błąd od razu.
    `post`, `sleep`, `clock`, `wall` podmienialne (testy bez sieci). Zwraca (JSON, liczba bajtów
    odpowiedzi); `wyslano_s` = czas zegara (`wall`) wysłania OSTATNIEJ próby.
    """

    def __init__(
        self,
        post: Callable[[str, dict], bytes] = _post,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        wall: Callable[[], float] = time.time,
        proby: int = PROBY,
    ) -> None:
        self._post, self._sleep, self._clock, self._wall = post, sleep, clock, wall
        self.proby = proby
        self.ponowienia = 0
        self.wyslano_s: float | None = None

    def __call__(self, body: dict, termin: float | None = None):
        ostatni: Exception | None = None
        for proba in range(self.proby):
            try:
                self.wyslano_s = self._wall()
                raw = self._post(INFO_URL, body)
                return parsuj(raw), len(raw)
            except urllib.error.HTTPError as e:  # przed OSError: HTTPError to też URLError
                if e.code not in RETRY_HTTP:
                    raise
                ostatni = e
            except ZaDuzaOdpowiedz:
                raise
            except BLEDY_PRZEJSCIOWE as e:
                ostatni = e
            if proba + 1 >= self.proby:
                break
            czekaj = opoznienie(proba)
            if termin is not None and self._clock() + czekaj > termin:
                break
            self.ponowienia += 1
            self._sleep(czekaj)
        assert ostatni is not None
        raise ostatni


# ------------------------------------------------------------------ zapis
class PisarzDzienny:
    """
    Dopisuje człon gzip na koniec pliku dnia UTC. Plik dotknięty pierwszy raz w tym procesie (start,
    nowy dzień, po błędzie zapisu) jest najpierw naprawiany (`napraw_ogon`). Nieudany zapis → plik
    przycięty do rozmiaru sprzed zapisu i wyjątek dalej.
    """

    def __init__(
        self,
        root: Path,
        log: Callable[[str], None] = lambda s: None,
        zapis: Callable[[int, bytes], int] = os.write,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._log = log
        self._zapis = zapis  # podmienialny w testach (symulacja pełnego dysku)
        self._naprawione: set[Path] = set()
        self.przyciete_bajty = 0

    def dopisz(self, czas_ms: int, linia: str) -> tuple[Path, int]:
        sciezka = plik_dnia(self.root, czas_ms)
        if sciezka not in self._naprawione:
            pelne, uciete = napraw_ogon(sciezka)
            if uciete:
                self.przyciete_bajty += uciete
                self._log(
                    f"naprawa {sciezka.name}: odcięto {uciete} B urwanego ogona ({pelne} pełnych migawek zostaje)"
                )
            self._naprawione.add(sciezka)
        czlon = czlon_gzip(linia.encode("ascii"))
        fd = os.open(sciezka, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            przed = os.fstat(fd).st_size
            try:
                n = self._zapis(fd, czlon)
                if n != len(czlon):
                    raise OSError(f"zapisano {n} z {len(czlon)} B")
                os.fsync(fd)
            except OSError:
                self._naprawione.discard(sciezka)  # następny zapis najpierw sprawdzi plik
                try:
                    os.ftruncate(fd, przed)
                except OSError:
                    pass
                raise
        finally:
            os.close(fd)
        return sciezka, len(czlon)


def zapisz_status(root: Path, **pola) -> Path:
    """`status.json` atomowo (plik tymczasowy + `os.replace`), JSON w ASCII."""
    sciezka = Path(root) / STATUS
    tmp = sciezka.with_name(STATUS + ".tmp")
    teraz = dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds")
    tmp.write_text(
        json.dumps({"zapisano_utc": teraz, **pola}, ensure_ascii=True, indent=1), encoding="ascii"
    )
    os.replace(tmp, sciezka)
    return sciezka


def _log_do_pliku(root: Path) -> Callable[[str], None]:
    def log(msg: str) -> None:
        teraz = dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds")
        try:
            with open(Path(root) / LOG, "a", encoding="utf-8") as f:
                f.write(f"{teraz} {msg}\n")
        except OSError:  # pełny dysk itp. — log nie może zatrzymać kolektora
            pass

    return log


def _czy_logowac(n: int) -> bool:
    return n <= LOG_PIERWSZE or n % LOG_CO == 0


# ------------------------------------------------------------------ pętla główna
def run(
    root: Path = DEFAULT_DIR,
    post: Callable[[str, dict], bytes] | None = None,
    sleep: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
    wall: Callable[[], float] | None = None,
    log: Callable[[str], None] | None = None,
    max_cycles: int | None = None,
    okres_s: float = OKRES_S,
) -> dict:
    """
    Pętla: czekaj do pełnej minuty → migawka (z ponowieniami do `termin`) → sprawdzenie → zapis członu
    → `status.json`. Kończy się po `max_cycles` cyklach (testy, krótka próba) albo gdy w katalogu pojawi
    się `WYLACZONY`; produkcyjnie `max_cycles=None` = zawsze. Zwraca stan (to samo co w `status.json`).
    """
    post = _post if post is None else post
    sleep = time.sleep if sleep is None else sleep
    clock = time.monotonic if clock is None else clock
    wall = time.time if wall is None else wall
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    log = _log_do_pliku(root) if log is None else log
    pisarz = PisarzDzienny(root, log=log)
    klient = Klient(post=post, sleep=sleep, clock=clock, wall=wall)
    stan: dict = {
        "start_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds"),
        "pid": os.getpid(),
        "zrodlo": INFO_URL,
        "zapytanie": ZAPYTANIE["type"],
        "okres_s": okres_s,
        "cykle": 0,
        "migawki": 0,
        "bledy_sieci": 0,
        "odrzucone": 0,
        "bledy_zapisu": 0,
        "ponowienia": 0,
        "przyciete_bajty": 0,
        "ostatnia_ms": None,
        "ostatnia_utc": None,
        "ostatni_plik": None,
        "ostatni_czlon_b": None,
        "ostatnia_odpowiedz_b": None,
        "monet": None,
        "ostatni_blad": None,
        "koniec": None,
    }
    bledy = [0]

    def status() -> None:
        stan.update(ponowienia=klient.ponowienia, przyciete_bajty=pisarz.przyciete_bajty)
        try:
            zapisz_status(root, **stan)
        except OSError as exc:  # status nie może zatrzymać kolektora (np. chwilowo pełny dysk)
            log(f"status.json niezapisany: {type(exc).__name__}: {str(exc)[:120]}")

    def blad(rodzaj: str, exc: BaseException) -> None:
        stan[rodzaj] += 1
        stan["ostatni_blad"] = f"{rodzaj}: {type(exc).__name__}: {str(exc)[:160]}"
        bledy[0] += 1
        if _czy_logowac(bledy[0]):
            log(f"błąd ({bledy[0]}): {stan['ostatni_blad']}")

    log(f"start pid {os.getpid()} → {root} ({INFO_URL}, co {okres_s:.0f} s)")
    try:
        while True:
            if (root / WYLACZNIK).exists():
                stan["koniec"] = "WYLACZONY"
                log("plik WYLACZONY — koniec pętli")
                break
            termin = nastepny_termin(wall(), okres_s)
            while (zostalo := termin - wall()) > 0:
                sleep(zostalo)
            if (root / WYLACZNIK).exists():
                stan["koniec"] = "WYLACZONY"
                log("plik WYLACZONY — koniec pętli")
                break
            try:
                odp, nbajt = klient(ZAPYTANIE, termin=clock() + okres_s - ZAPAS_S)
            except ValueError as exc:  # odpowiedź przyszła, ale zła: NaN/Infinity, ucięta, za duża
                blad("odrzucone", exc)
            except Exception as exc:  # noqa: BLE001 — błąd jednej migawki nie przerywa pętli
                blad("bledy_sieci", exc)
            else:
                czas_ms = int(round(wall() * 1000))
                wyslano_ms = int(round(klient.wyslano_s * 1000))
                try:
                    monet = sprawdz_odpowiedz(odp)
                    linia = rekord(czas_ms, wyslano_ms, odp)
                    plik_dnia(root, czas_ms)  # zakres czasu przed zapisem (ValueError = odrzucona)
                except (ValueError, TypeError) as exc:
                    blad("odrzucone", exc)
                else:
                    try:
                        sciezka, nczlon = pisarz.dopisz(czas_ms, linia)
                    except OSError as exc:
                        blad("bledy_zapisu", exc)
                    else:
                        stan["migawki"] += 1
                        stan.update(
                            ostatnia_ms=czas_ms,
                            ostatnia_utc=czas_utc(czas_ms),
                            ostatni_plik=sciezka.name,
                            ostatni_czlon_b=nczlon,
                            ostatnia_odpowiedz_b=nbajt,
                            monet=monet,
                        )
                        if stan["migawki"] % PODSUMOWANIE_CO == 0:
                            log(
                                f"migawek {stan['migawki']} (błędów sieci {stan['bledy_sieci']}, "
                                f"odrzuconych {stan['odrzucone']}, zapisu {stan['bledy_zapisu']}); "
                                f"ostatnia {nczlon} B gzip, {monet} monet"
                            )
            stan["cykle"] += 1
            status()
            if max_cycles is not None and stan["cykle"] >= max_cycles:
                stan["koniec"] = f"max_cycles={max_cycles}"
                break
    finally:
        if stan["koniec"] is None:
            stan["koniec"] = "przerwanie"
        log(f"koniec: {stan['koniec']}; migawek {stan['migawki']}, cykli {stan['cykle']}")
        status()
    return stan


# ------------------------------------------------------------------ blokada i nadzór
def zablokuj(root: Path, fd: int | None = None) -> int | None:
    """
    Jedna instancja: `flock` (wyłączny, bez czekania) na `<root>/.lock`. `fd` = deskryptor odziedziczony
    po powłoce nadzoru (`--blokada-fd`) — musi wskazywać ten sam plik (inaczej ValueError); blokada na
    nim jest już nasza albo wolna. Zwraca deskryptor trzymający blokadę albo None (trzyma ją kto inny).
    """
    import fcntl  # tylko Linux/Unix — kolektor działa na serwerze

    sciezka = Path(root) / BLOKADA
    wlasny = fd is None
    if wlasny:
        fd = os.open(sciezka, os.O_RDWR | os.O_CREAT, 0o644)
    else:
        a, b = os.fstat(fd), os.stat(sciezka)
        if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
            raise ValueError(f"hl stan: --blokada-fd {fd} nie wskazuje {sciezka}")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        if wlasny:
            os.close(fd)
        return None
    return fd


def status_text(root: Path, teraz_s: float | None = None) -> str:
    """Stan kolektora dla człowieka: `status.json` + plik dzisiejszy (rozmiar, pełne migawki) + wyłącznik."""
    root = Path(root)
    teraz_s = time.time() if teraz_s is None else teraz_s
    wyl = (
        " WYŁĄCZNIK: plik WYLACZONY istnieje (cron nie startuje kolektora)."
        if (root / WYLACZNIK).exists()
        else ""
    )
    p = root / STATUS
    if not p.exists():
        return f"brak {p} — kolektor jeszcze nic nie zapisał.{wyl}"
    st = json.loads(p.read_text(encoding="ascii"))
    ostatnia = st.get("ostatnia_ms")
    if ostatnia:
        wiek = teraz_s - ostatnia / 1000.0
        ost = f"{st.get('ostatnia_utc')} ({wiek:.0f} s temu)"
        if wiek > STARY_STATUS_S:
            ost += " — UWAGA: brak świeżych migawek"
    else:
        ost = "-"
    dzis = plik_dnia(root, int(teraz_s * 1000))
    if dzis.exists():
        dane = dzis.read_bytes()
        koniec, n = koniec_pelnych_czlonow(dane)
        ogon = f", urwany ogon {len(dane) - koniec} B" if koniec < len(dane) else ""
        plik = f"{dzis.name}: {len(dane) / 1e6:.2f} MB, pełnych migawek {n}{ogon}"
    else:
        plik = f"{dzis.name}: brak"
    return (
        f"kolektor HL pid {st.get('pid')} od {st.get('start_utc')}; status z {st.get('zapisano_utc')}; "
        f"migawek {st.get('migawki')} w {st.get('cykle')} cyklach (błędy sieci {st.get('bledy_sieci')}, "
        f"odrzucone {st.get('odrzucone')}, zapisu {st.get('bledy_zapisu')}, ponowień {st.get('ponowienia')}); "
        f"ostatnia {ost}, {st.get('ostatni_czlon_b')} B gzip, monet {st.get('monet')}; "
        f"ostatni błąd: {st.get('ostatni_blad')}; koniec: {st.get('koniec')}; dziś {plik}.{wyl}"
    )


def _domyslny_katalog() -> Path:
    env = os.environ.get(ENV_DIR)
    return Path(env).expanduser() if env else DEFAULT_DIR


def _stop(signum, frame) -> None:
    """SIGTERM → zwykłe wyjście (blok `finally` w `run` zapisze status i wpis w logu)."""
    raise SystemExit(0)


def main(argv: list[str]) -> int:
    root = _domyslny_katalog()
    pokaz = False
    max_cycles: int | None = None
    fd: int | None = None
    it = iter(argv)
    try:
        for a in it:
            if a == "--dir":
                root = Path(next(it)).expanduser()
            elif a == "--status":
                pokaz = True
            elif a == "--max-cycles":
                max_cycles = int(next(it))
                if max_cycles < 1:
                    raise ValueError("--max-cycles: co najmniej 1")
            elif a == "--blokada-fd":
                fd = int(next(it))
                if fd < 0:
                    raise ValueError("--blokada-fd: deskryptor ≥ 0")
            else:
                print(f"nieznany argument {a!r}", file=sys.stderr)
                return 2
    except (StopIteration, ValueError) as exc:
        print(f"zły argument: {exc or 'brak wartości'}", file=sys.stderr)
        return 2
    if pokaz:
        print(status_text(root))
        return 0
    root.mkdir(parents=True, exist_ok=True)
    if (root / WYLACZNIK).exists():
        print(f"{root / WYLACZNIK} istnieje — kolektor nie startuje")
        return 0
    try:
        blokada = zablokuj(root, fd)
    except (OSError, ValueError) as exc:
        print(f"blokada: {exc}", file=sys.stderr)
        return 1
    if blokada is None:
        print(f"inna instancja trzyma {root / BLOKADA} — koniec")
        return 0
    signal.signal(signal.SIGTERM, _stop)
    try:
        run(root, max_cycles=max_cycles)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
