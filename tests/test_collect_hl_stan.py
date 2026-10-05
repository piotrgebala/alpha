"""
Testy kolektora stanu rynku Hyperliquid (`data/collect_hl_stan.py`, runda HS0) — BEZ SIECI: fałszywe
`post`, `sleep`, `clock` i `wall` (jeden zegar testu, sen przesuwa czas) + `max_cycles`.

Sprawdzają: zapis pełnej odpowiedzi i czasów jako człony gzip w pliku dnia UTC (czytelne `gzip.open`
i, gdy jest, systemowym `gzip`), JSON w ASCII, rytm na pełnej minucie, zmianę dnia, odrzucenie złej
odpowiedzi i czasu spoza 2019–2100 bez przerwania pętli, ponowienia po 429/5xx z odczekaniem (i ich brak po
innych 4xx, `NaN`, za dużej odpowiedzi), limit ponowień do następnej migawki, wyłącznik `WYLACZONY`,
naprawę urwanego ogona pliku, cofnięcie nieudanego zapisu, `status.json` (atomowo, ASCII) i `--status`,
blokadę jednej instancji (własną i odziedziczoną po powłoce), odrzucenie adresu innego niż
`https://api.hyperliquid.xyz/info`, limit rozmiaru, weryfikację certyfikatu i brak przekierowań.
Właściwości (`hypothesis`): ścieżka pliku z czasu, termin migawki, odczekanie w granicach, naprawa ogona,
odrzucenie złej odpowiedzi, rekord ASCII bez straty treści.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from data import collect_hl_stan as hs
from data import liquidation_time as lt

UTC = dt.timezone.utc
T0 = dt.datetime(2026, 10, 5, 12, 0, 30, tzinfo=UTC).timestamp()
ZAPYTANIE = {"type": "metaAndAssetCtxs"}
na_linuksie = pytest.mark.skipif(sys.platform == "win32", reason="flock tylko na Linux/Unix")


def _odp(n: int = 3, nazwa: str = "C") -> list:
    uni = [{"name": f"{nazwa}{i}", "szDecimals": 2, "maxLeverage": 10} for i in range(n)]
    ctxs = [
        {"funding": "0.0000125", "markPx": "1.5", "midPx": "1.5", "openInterest": "5.0"}
        for _ in range(n)
    ]
    return [{"universe": uni, "marginTables": []}, ctxs]


class Zegar:
    """Jeden fałszywy czas dla `wall`, `clock` i `sleep` (sen przesuwa czas, nic nie śpi naprawdę)."""

    def __init__(self, t: float = T0) -> None:
        self.t = t
        self.sny: list[float] = []

    def wall(self) -> float:
        return self.t

    def clock(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sny.append(s)
        self.t += s


def _http(kod: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(hs.INFO_URL, kod, f"HTTP {kod}", {}, None)


def _post_seq(zegar: Zegar, *odpowiedzi, czas_s: float = 0.2):
    """Kolejne wywołania → kolejne odpowiedzi (bajty, obiekt JSON albo wyjątek); ostatnia się powtarza.
    Każde wywołanie trwa `czas_s` sekund zegara testu."""
    lista = list(odpowiedzi)
    wywolania: list[tuple[str, dict, float]] = []

    def post(url, body):
        wywolania.append((url, body, zegar.t))
        item = lista.pop(0) if len(lista) > 1 else lista[0]
        zegar.t += czas_s
        if isinstance(item, BaseException):
            raise item
        if callable(item):
            item = item()
        if isinstance(item, (bytes, bytearray)):
            return bytes(item)
        return json.dumps(item).encode("ascii")

    post.wywolania = wywolania
    return post


def _run(root: Path, *odpowiedzi, cykle: int | None = 3, zegar: Zegar | None = None, czas_s=0.2):
    zegar = zegar or Zegar()
    post = _post_seq(zegar, *odpowiedzi, czas_s=czas_s)
    logi: list[str] = []
    stan = hs.run(
        root,
        post=post,
        sleep=zegar.sleep,
        clock=zegar.clock,
        wall=zegar.wall,
        log=logi.append,
        max_cycles=cykle,
    )
    return stan, post, zegar, logi


def _ms(*args) -> int:
    return int(round(dt.datetime(*args, tzinfo=UTC).timestamp() * 1000))


# ------------------------------------------------------------------ pętla i zapis
def test_trzy_migawki_na_pelnych_minutach_w_pliku_dnia(tmp_path):
    stan, post, _, _ = _run(tmp_path, _odp())
    plik = tmp_path / "2026-10-05.jsonl.gz"
    rek = hs.czytaj_dzien(plik)
    assert len(rek) == 3
    # zapytania na pełnych minutach, stały adres i treść zapytania
    starty = [w[2] for w in post.wywolania]
    assert starty == pytest.approx([T0 + 30, T0 + 90, T0 + 150], abs=1e-3)
    assert all(w[0] == hs.INFO_URL and w[1] == ZAPYTANIE for w in post.wywolania)
    assert [r["wyslano_ms"] for r in rek] == [
        _ms(2026, 10, 5, 12, 1),
        _ms(2026, 10, 5, 12, 2),
        _ms(2026, 10, 5, 12, 3),
    ]
    assert [r["czas_ms"] - r["wyslano_ms"] for r in rek] == [200, 200, 200]
    assert rek[0]["czas_utc"] == "2026-10-05T12:01:00.200+00:00"
    assert all(r["odpowiedz"] == _odp() for r in rek)
    # trzy osobne człony gzip, cały plik pełny
    dane = plik.read_bytes()
    assert hs.koniec_pelnych_czlonow(dane) == (len(dane), 3)
    assert stan["migawki"] == 3 and stan["cykle"] == 3
    assert stan["bledy_sieci"] == stan["odrzucone"] == stan["bledy_zapisu"] == 0
    assert stan["monet"] == 3 and stan["ostatni_plik"] == plik.name
    assert stan["koniec"] == "max_cycles=3"


@pytest.mark.skipif(not shutil.which("gzip"), reason="brak systemowego gzip")
def test_plik_czytelny_systemowym_gzip(tmp_path):
    _run(tmp_path, _odp())
    plik = tmp_path / "2026-10-05.jsonl.gz"
    assert subprocess.run(["gzip", "-t", str(plik)], check=False).returncode == 0
    out = subprocess.run(["gzip", "-dc", str(plik)], capture_output=True, check=True).stdout
    linie = out.splitlines()
    assert len(linie) == 3
    assert json.loads(linie[2])["odpowiedz"] == _odp()


def test_json_w_ascii_mimo_znakow_spoza_ascii(tmp_path):
    odp = _odp(nazwa="ŻÓŁW-Ω")
    _run(tmp_path, odp, cykle=1)
    surowe = gzip.decompress((tmp_path / "2026-10-05.jsonl.gz").read_bytes())
    assert surowe.isascii() and b"\\u017b" in surowe
    assert json.loads(surowe)["odpowiedz"] == odp
    assert (tmp_path / hs.STATUS).read_bytes().isascii()


def test_zmiana_dnia_utc_daje_dwa_pliki(tmp_path):
    zegar = Zegar(dt.datetime(2026, 10, 5, 23, 58, 30, tzinfo=UTC).timestamp())
    _run(tmp_path, _odp(), zegar=zegar)
    assert len(hs.czytaj_dzien(tmp_path / "2026-10-05.jsonl.gz")) == 1  # 23:59
    assert len(hs.czytaj_dzien(tmp_path / "2026-10-06.jsonl.gz")) == 2  # 00:00, 00:01


def test_zla_odpowiedz_odrzucona_petla_idzie_dalej(tmp_path):
    stan, _, _, logi = _run(tmp_path, _odp(), {"error": "x"}, _odp())
    assert len(hs.czytaj_dzien(tmp_path / "2026-10-05.jsonl.gz")) == 2
    assert stan["odrzucone"] == 1 and stan["migawki"] == 2 and stan["cykle"] == 3
    assert "odrzucone" in stan["ostatni_blad"] and any("błąd" in s for s in logi)


def test_429_i_5xx_ponowione_z_rosnacym_odczekaniem(tmp_path):
    stan, post, zegar, _ = _run(tmp_path, _http(429), _http(503), _odp())
    assert stan["migawki"] == 3 and stan["ponowienia"] == 2 and stan["bledy_sieci"] == 0
    assert [s for s in zegar.sny if s in (2.0, 4.0)] == [2.0, 4.0]
    assert len(post.wywolania) == 5


def test_inne_4xx_bez_ponowien(tmp_path):
    stan, post, _, _ = _run(tmp_path, _http(400))
    assert stan["ponowienia"] == 0 and stan["bledy_sieci"] == 3 and len(post.wywolania) == 3
    assert not list(tmp_path.glob("*.jsonl.gz"))
    assert "HTTP 400" in stan["ostatni_blad"]


def test_nan_odrzucony_bez_ponowien(tmp_path):
    stan, post, _, _ = _run(tmp_path, b'[{"universe":[{"name":"A"}]},[{"x":NaN}]]', cykle=1)
    assert stan["ponowienia"] == 0 and stan["odrzucone"] == 1 and len(post.wywolania) == 1
    assert stan["bledy_sieci"] == 0 and not list(tmp_path.glob("*.jsonl.gz"))


def test_uciety_json_ponowiony(tmp_path):
    stan, post, _, _ = _run(tmp_path, b'[{"universe":', _odp(), cykle=1)
    assert stan["migawki"] == 1 and stan["ponowienia"] == 1 and len(post.wywolania) == 2


def test_ponowienia_koncza_sie_przed_nastepna_migawka(tmp_path):
    # każde zapytanie trwa 20 s i pada; termin ponowień = start cyklu + 60 − 10 s
    stan, post, _, _ = _run(tmp_path, urllib.error.URLError("brak sieci"), czas_s=20.0)
    assert stan["bledy_sieci"] == 3 and stan["migawki"] == 0
    assert stan["ponowienia"] == 2 * 3  # 20 + 2 + 20 + 4 = 46 s < 50; następne 8 s by przekroczyło
    starty = [w[2] for w in post.wywolania]
    assert len(starty) == 9 and len({int(t // 60) for t in starty}) == 3  # 3 próby w każdej minucie
    assert all(t % 60.0 <= 60.0 - hs.ZAPAS_S for t in starty)


def test_wylacznik_zatrzymuje_petle(tmp_path):
    def i_wylacz():
        (tmp_path / hs.WYLACZNIK).write_text("", encoding="ascii")
        return _odp()

    stan, post, _, logi = _run(tmp_path, i_wylacz, cykle=None)
    assert stan["koniec"] == "WYLACZONY" and stan["migawki"] == 1 and len(post.wywolania) == 1
    assert any("WYLACZONY" in s for s in logi)


def test_wylacznik_przed_startem_zero_zapytan(tmp_path):
    (tmp_path / hs.WYLACZNIK).write_text("", encoding="ascii")
    stan, post, _, _ = _run(tmp_path, _odp(), cykle=None)
    assert stan["koniec"] == "WYLACZONY" and post.wywolania == []


def test_zegar_spoza_2019_2100_odrzucony_bez_pliku(tmp_path):
    stan, _, _, _ = _run(tmp_path, _odp(), zegar=Zegar(1_000.0))  # 1970
    assert stan["odrzucone"] == 3 and stan["migawki"] == 0
    assert not list(tmp_path.glob("*.jsonl.gz"))
    assert "poza zakresem" in stan["ostatni_blad"]


def test_urwany_ogon_naprawiony_przy_starcie(tmp_path):
    plik = tmp_path / "2026-10-05.jsonl.gz"
    c1 = hs.czlon_gzip(b'{"a":1}\n')
    c2 = hs.czlon_gzip(b'{"a":2}\n')
    c3 = hs.czlon_gzip(b'{"a":3}\n')
    plik.write_bytes(c1 + c2 + c3[: len(c3) // 2])
    stan, _, _, logi = _run(tmp_path, _odp(), cykle=1)
    dane = plik.read_bytes()
    assert hs.koniec_pelnych_czlonow(dane) == (len(dane), 3)
    linie = gzip.decompress(dane).splitlines()
    assert linie[:2] == [b'{"a":1}', b'{"a":2}'] and json.loads(linie[2])["odpowiedz"] == _odp()
    assert stan["przyciete_bajty"] == len(c3) // 2
    assert any("naprawa" in s for s in logi)


def test_blad_zapisu_cofa_czlon_i_nastepny_zapis_dziala(tmp_path):
    wywolania = [0]

    def zapis(fd, dane):
        wywolania[0] += 1
        if wywolania[0] == 2:  # pełny dysk w połowie członu
            os.write(fd, dane[: len(dane) // 2])
            raise OSError(28, "No space left on device")
        return os.write(fd, dane)

    p = hs.PisarzDzienny(tmp_path, zapis=zapis)
    ms = _ms(2026, 10, 5, 12, 0)
    sciezka, _ = p.dopisz(ms, '{"n":1}\n')
    rozmiar = sciezka.stat().st_size
    with pytest.raises(OSError):
        p.dopisz(ms, '{"n":2}\n')
    assert sciezka.stat().st_size == rozmiar  # urwany człon cofnięty
    p.dopisz(ms, '{"n":3}\n')
    assert hs.czytaj_dzien(sciezka) == [{"n": 1}, {"n": 3}]


def test_blad_zapisu_w_petli_liczony_petla_dalej(tmp_path):
    (tmp_path / "2026-10-05.jsonl.gz").mkdir()  # w miejscu pliku katalog → OSError przy zapisie
    stan, _, _, _ = _run(tmp_path, _odp())
    assert stan["bledy_zapisu"] == 3 and stan["cykle"] == 3 and stan["migawki"] == 0


def test_status_json_atomowy_i_kompletny(tmp_path):
    stan, _, _, _ = _run(tmp_path, _odp())
    st_plik = json.loads((tmp_path / hs.STATUS).read_text(encoding="ascii"))
    assert not (tmp_path / (hs.STATUS + ".tmp")).exists()
    for k in (
        "migawki",
        "cykle",
        "bledy_sieci",
        "odrzucone",
        "bledy_zapisu",
        "ponowienia",
        "koniec",
    ):
        assert st_plik[k] == stan[k]
    assert st_plik["zrodlo"] == hs.INFO_URL and st_plik["ostatnia_ms"] == stan["ostatnia_ms"]


def test_status_text(tmp_path):
    assert "brak" in hs.status_text(tmp_path)
    stan, _, zegar, _ = _run(tmp_path, _odp())
    tekst = hs.status_text(tmp_path, teraz_s=zegar.t)
    assert "migawek 3" in tekst and "pełnych migawek 3" in tekst and "UWAGA" not in tekst
    assert "UWAGA" in hs.status_text(tmp_path, teraz_s=zegar.t + 600)
    (tmp_path / hs.WYLACZNIK).write_text("", encoding="ascii")
    assert "WYŁĄCZNIK" in hs.status_text(tmp_path, teraz_s=zegar.t)


# ------------------------------------------------------------------ sieć: adres, limit, TLS
@pytest.mark.parametrize(
    "url",
    [
        "http://api.hyperliquid.xyz/info",
        "https://api.hyperliquid.xyz.evil.example/info",
        "https://evil.example/info",
        "https://api.hyperliquid.xyz/exchange",
        "https://user@api.hyperliquid.xyz/info",
        "https://api.hyperliquid.xyz:8443/info",
        "ftp://api.hyperliquid.xyz/info",
        "wss://api.hyperliquid.xyz/ws",
    ],
)
def test_post_odrzuca_adres_inny_niz_https_info(url, monkeypatch):
    def nie_wolno():
        raise AssertionError("nie wolno otwierać połączenia")

    monkeypatch.setattr(hs, "_opener", nie_wolno)
    with pytest.raises(ValueError):
        hs._post(url, ZAPYTANIE)


class _Odp:
    def __init__(self, cialo: bytes, naglowki: dict) -> None:
        self._cialo, self.headers = cialo, naglowki

    def read(self, n: int = -1) -> bytes:
        return self._cialo if n < 0 else self._cialo[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _falszywy_opener(cialo: bytes, naglowki: dict, zadania: list):
    class Opener:
        def open(self, req, timeout=None):
            zadania.append((req, timeout))
            return _Odp(cialo, naglowki)

    return lambda: Opener()


def test_post_wysyla_json_i_zwraca_bajty(monkeypatch):
    zadania: list = []
    monkeypatch.setattr(hs, "_opener", _falszywy_opener(b"[1,2]", {}, zadania))
    assert hs._post(hs.INFO_URL, ZAPYTANIE) == b"[1,2]"
    req, timeout = zadania[0]
    assert req.full_url == hs.INFO_URL and req.get_method() == "POST"
    assert json.loads(req.data) == ZAPYTANIE and timeout == hs.TIMEOUT_S


def test_post_limit_rozmiaru(monkeypatch):
    monkeypatch.setattr(hs, "_opener", _falszywy_opener(b"[]", {"Content-Length": "999999999"}, []))
    with pytest.raises(hs.ZaDuzaOdpowiedz):
        hs._post(hs.INFO_URL, ZAPYTANIE)
    monkeypatch.setattr(hs, "_opener", _falszywy_opener(b"x" * 101, {}, []))
    with pytest.raises(hs.ZaDuzaOdpowiedz):
        hs._post(hs.INFO_URL, ZAPYTANIE, limit=100)
    assert hs._post(hs.INFO_URL, ZAPYTANIE, limit=101) == b"x" * 101


def test_za_duza_odpowiedz_bez_ponowien(tmp_path):
    stan, post, _, _ = _run(tmp_path, hs.ZaDuzaOdpowiedz("za duża"), cykle=1)
    assert stan["ponowienia"] == 0 and stan["odrzucone"] == 1 and len(post.wywolania) == 1


def test_opener_weryfikuje_certyfikat_bez_proxy_i_bez_przekierowan():
    opener = hs._opener()
    https = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPSHandler)]
    assert len(https) == 1
    ctx = https[0]._context
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname
    proxy = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
    assert all(h.proxies == {} for h in proxy)
    przek = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
    assert przek and all(isinstance(h, hs._BezPrzekierowan) for h in przek)
    req = urllib.request.Request(hs.INFO_URL, data=b"{}")
    assert hs._BezPrzekierowan().redirect_request(req, None, 302, "Found", {}, "http://x/") is None


# ------------------------------------------------------------------ blokada i main
@na_linuksie
def test_blokada_jednej_instancji_wlasna_i_odziedziczona(tmp_path):
    fd = hs.zablokuj(tmp_path)
    assert fd is not None
    try:
        assert hs.zablokuj(tmp_path) is None  # druga instancja (nowy deskryptor) — odmowa
        assert hs.zablokuj(tmp_path, fd) == fd  # deskryptor odziedziczony, blokada już nasza
        inny = os.open(tmp_path / "inny", os.O_RDWR | os.O_CREAT)
        try:
            with pytest.raises(ValueError):
                hs.zablokuj(tmp_path, inny)  # deskryptor innego pliku
        finally:
            os.close(inny)
    finally:
        os.close(fd)
    fd2 = hs.zablokuj(tmp_path)  # po zwolnieniu — znów można
    assert fd2 is not None
    os.close(fd2)


def test_main_bledne_argumenty(tmp_path, capsys):
    assert hs.main(["--nieznany"]) == 2
    assert hs.main(["--max-cycles", "0"]) == 2
    assert hs.main(["--max-cycles"]) == 2
    assert hs.main(["--blokada-fd", "-1"]) == 2
    assert hs.main(["--dir"]) == 2


def test_main_status_bez_sieci(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(hs, "run", lambda *a, **k: pytest.fail("--status nie uruchamia pętli"))
    assert hs.main(["--dir", str(tmp_path), "--status"]) == 0
    assert "brak" in capsys.readouterr().out


def test_main_katalog_z_zmiennej_srodowiska(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv(hs.ENV_DIR, str(tmp_path / "z_env"))
    assert hs.main(["--status"]) == 0
    assert "z_env" in capsys.readouterr().out


def test_main_wylacznik_nie_startuje(tmp_path, monkeypatch):
    (tmp_path / hs.WYLACZNIK).write_text("", encoding="ascii")
    monkeypatch.setattr(hs, "run", lambda *a, **k: pytest.fail("WYLACZONY — pętla nie rusza"))
    assert hs.main(["--dir", str(tmp_path)]) == 0


@na_linuksie
def test_main_druga_instancja_konczy_sie_od_razu(tmp_path, monkeypatch):
    monkeypatch.setattr(hs, "run", lambda *a, **k: pytest.fail("druga instancja nie rusza"))
    fd = hs.zablokuj(tmp_path)
    try:
        assert hs.main(["--dir", str(tmp_path)]) == 0
    finally:
        os.close(fd)


@na_linuksie
def test_main_z_blokada_odziedziczona_po_powloce(tmp_path, monkeypatch):
    import fcntl

    wywolane: list = []
    monkeypatch.setattr(hs, "run", lambda root, **k: wywolane.append((root, k)))
    monkeypatch.setattr(
        hs.signal, "signal", lambda *a: None
    )  # bez zmiany obsługi SIGTERM w pyteście
    fd = os.open(tmp_path / hs.BLOKADA, os.O_RDWR | os.O_CREAT)  # jak `exec 7>…/.lock` w powłoce
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        argv = ["--dir", str(tmp_path), "--blokada-fd", str(fd), "--max-cycles", "2"]
        assert hs.main(argv) == 0
        assert wywolane == [(tmp_path, {"max_cycles": 2})]
        inny = os.open(tmp_path / "inny", os.O_RDWR | os.O_CREAT)
        try:
            argv = ["--dir", str(tmp_path), "--blokada-fd", str(inny)]
            assert hs.main(argv) == 1  # deskryptor nie wskazuje .lock
        finally:
            os.close(inny)
    finally:
        os.close(fd)


# ------------------------------------------------------------------ właściwości (hypothesis)
@given(st.integers(min_value=lt.MIN_EVENT_MS, max_value=lt.MAX_EVENT_MS))
@settings(max_examples=200, deadline=None)
def test_wlasciwosc_plik_dnia_z_czasu(ms):
    p = hs.plik_dnia(Path("/x"), ms)
    dzien = dt.datetime.fromtimestamp(ms / 1000, tz=UTC).date()
    assert p == Path("/x") / f"{dzien.isoformat()}.jsonl.gz"


@given(
    st.one_of(
        st.integers(max_value=lt.MIN_EVENT_MS - 1),
        st.integers(min_value=lt.MAX_EVENT_MS + 1),
        st.booleans(),
        st.text(max_size=5),
        st.none(),
    )
)
@settings(max_examples=200, deadline=None)
def test_wlasciwosc_czas_spoza_zakresu_odrzucony(ms):
    with pytest.raises(ValueError):
        hs.plik_dnia(Path("/x"), ms)


@given(
    st.floats(min_value=1.5e9, max_value=4.1e9, allow_nan=False),
    st.sampled_from([1.0, 30.0, 60.0, 3600.0]),
)
@settings(max_examples=300, deadline=None)
def test_wlasciwosc_termin_migawki(teraz, okres):
    termin = hs.nastepny_termin(teraz, okres)
    assert termin > teraz and termin - teraz <= okres + 1e-6
    assert termin % okres == 0


@given(st.integers(min_value=0, max_value=10_000))
@settings(max_examples=200, deadline=None)
def test_wlasciwosc_odczekanie_w_granicach(proba):
    w = hs.opoznienie(proba)
    assert 0 < w <= hs.BACKOFF_MAX_S
    assert hs.opoznienie(proba + 1) >= w


@given(
    st.lists(st.text(max_size=40), min_size=0, max_size=6),
    st.one_of(
        st.integers(min_value=0, max_value=10_000),  # urwany człon: ile bajtów zostało
        st.binary(min_size=1, max_size=64),  # śmieci po awarii
    ),
)
@settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_wlasciwosc_naprawa_ogona(tmp_path, linie, ogon):
    pelne = b"".join(hs.czlon_gzip((json.dumps(s) + "\n").encode("ascii")) for s in linie)
    if isinstance(ogon, int):
        nastepny = hs.czlon_gzip(b'{"urwany":true}\n')
        ogon = nastepny[: ogon % len(nastepny)]
    dane = pelne + ogon
    assert hs.koniec_pelnych_czlonow(dane) == (len(pelne), len(linie))
    plik = tmp_path / "dzien.jsonl.gz"
    plik.write_bytes(dane)
    assert hs.napraw_ogon(plik) == (len(linie), len(ogon))
    with open(plik, "ab") as f:
        f.write(hs.czlon_gzip(b'{"po":1}\n'))
    tekst = gzip.decompress(plik.read_bytes()).decode("ascii").splitlines()
    assert [json.loads(t) for t in tekst] == [*linie, {"po": 1}]


JSON = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(),
    lambda dzieci: st.lists(dzieci, max_size=4)
    | st.dictionaries(st.text(max_size=8), dzieci, max_size=4),
    max_leaves=20,
)


@given(JSON)
@settings(max_examples=300, deadline=None)
def test_wlasciwosc_zla_odpowiedz_odrzucona_tylko_valueerror(odp):
    try:
        n = hs.sprawdz_odpowiedz(odp)
    except ValueError:
        return
    meta, ctxs = odp  # przyjęta → kształt naprawdę poprawny
    assert n == len(meta["universe"]) == len(ctxs) > 0
    assert all(isinstance(m["name"], str) and m["name"] for m in meta["universe"])
    assert all(isinstance(c, dict) for c in ctxs)


@given(
    st.lists(
        st.fixed_dictionaries({"name": st.text(min_size=1, max_size=10)}), min_size=1, max_size=5
    ).flatmap(
        lambda uni: st.tuples(
            st.just(uni),
            st.lists(
                st.dictionaries(st.text(max_size=6), JSON, max_size=3),
                min_size=len(uni),
                max_size=len(uni),
            ),
        )
    )
)
@settings(max_examples=200, deadline=None)
def test_wlasciwosc_rekord_ascii_bez_straty_tresci(para):
    uni, ctxs = para
    odp = [{"universe": uni}, ctxs]
    assert hs.sprawdz_odpowiedz(odp) == len(uni)
    linia = hs.rekord(_ms(2026, 10, 5, 12, 0), _ms(2026, 10, 5, 11, 59, 59), odp)
    assert linia.isascii() and linia.endswith("\n") and linia.count("\n") == 1
    assert json.loads(linia)["odpowiedz"] == odp
