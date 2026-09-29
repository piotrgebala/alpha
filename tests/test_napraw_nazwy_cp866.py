"""Testy tools/napraw_nazwy_cp866.py (zadanie 024) — tylko sztuczne katalogi w `tmp_path`.

Nazwy plików tworzone z BAJTÓW (`os.fsencode`, ścieżki bytes), tak jak na serwerze: cztery prawdziwe
zniekształcone nazwy z `data/raw/universe_full` wpisane dosłownie jako bajty (regresja), plus test
właściwości: zniekształcenie cp866 dowolnej nazwy spoza ASCII da się odwrócić, a odwrócona nazwa nie
jest już kandydatem (drugi przebieg nic nie zmienia).
"""

from __future__ import annotations

import os

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import napraw_nazwy_cp866 as nn

# Dosłowne bajty nazw z serwera (data/raw/universe_full, 2026-09-29) → poprawne nazwy.
SERWER = {
    b"\xd1\x85\xe2\x95\x95\xd0\x91\xd1\x85\xd0\xbe\xd0\x99\xd1\x84\xe2\x95\x91\xe2\x95\x91"
    b"\xd1\x87\xd0\xa4\xd0\xafUSDT_1d.parquet": "币安人生USDT_1d.parquet",
    b"\xd1\x86\xd0\x98\xd0\xa1\xd1\x88\xe2\x95\x95\xd0\x9f\xd1\x89\xd0\xb9\xd0\xbc\xd1\x86"
    b"\xd0\xad\xd0\xb5\xd1\x84\xe2\x95\x91\xd0\x96USDT_funding.parquet": "我踏马来了USDT_funding.parquet",
    b"\xd1\x87\xd0\x99\xd0\xab\xd1\x86\xd0\xad\xd0\xb5USDT_1d.parquet": "牛来USDT_1d.parquet",
    b"\xd1\x89\xe2\x95\x9b\xd0\xa9\xd1\x88\xd0\xa9\xe2\x95\x9bUSDT_1d.parquet": "龙虾USDT_1d.parquet",
    b"\xd1\x85\xd0\xa3\xd0\x98\xd1\x85\xd0\xaf\xe2\x95\x91\xd1\x87\xe2\x96\x92\xe2\x94\x82"
    b"USDT_1d.parquet": "哈基米USDT_1d.parquet",
}


def znieksztalc(nazwa: str) -> bytes:
    """Mechanizm z serwera: bajty UTF-8 odczytane jako cp866 i zapisane w UTF-8."""
    return nazwa.encode("utf-8").decode("cp866").encode("utf-8")


def _plik(katalog, nazwa: bytes, tresc: bytes) -> bytes:
    sciezka = os.path.join(os.fsencode(katalog), nazwa)
    with open(sciezka, "wb") as f:
        f.write(tresc)
    return sciezka


def _stan(katalog) -> dict[bytes, tuple[bytes, int]]:
    """Nazwa (bajty) → (treść, mtime_ns) — do porównań „przed/po”."""
    kb = os.fsencode(katalog)
    out = {}
    for n in os.listdir(kb):
        p = os.path.join(kb, n)
        with open(p, "rb") as f:
            out[n] = (f.read(), os.stat(p).st_mtime_ns)
    return out


@pytest.fixture
def ref_csv(tmp_path):
    p = tmp_path / "events.csv"
    pd.DataFrame({"symbol": ["币安人生USDT", "我踏马来了USDT", "BTCUSDT"]}).to_csv(
        p, index=False, encoding="utf-8"
    )
    return str(p)


@pytest.fixture
def katalog(tmp_path):
    d = tmp_path / "universe_full"
    d.mkdir()
    _plik(d, znieksztalc("币安人生USDT_1d.parquet"), b"swiece-binance-zycie")
    _plik(d, znieksztalc("币安人生USDT_funding.parquet"), b"funding-binance-zycie")
    _plik(d, b"BTCUSDT_1d.parquet", b"btc")
    _plik(d, "我踏马来了USDT_1d.parquet".encode("utf-8"), b"juz-poprawna")
    return str(d)


# --- funkcje czyste -------------------------------------------------------------------------


@pytest.mark.parametrize("stara,nowa", sorted(SERWER.items()))
def test_odwroc_prawdziwe_nazwy_z_serwera(stara, nowa):
    assert nn.odwroc_cp866(stara) == nowa.encode("utf-8")
    assert znieksztalc(nowa) == stara  # mechanizm zniekształcenia potwierdzony co do bajtu


@pytest.mark.parametrize(
    "nazwa",
    [
        b"BTCUSDT_1d.parquet",  # ASCII
        "币安人生USDT_1d.parquet".encode("utf-8"),  # poprawna (znaków CJK nie ma w cp866)
        "Отчёт_1d.parquet".encode("utf-8"),  # poprawna cyrylica: odwrócenie nie daje UTF-8
        b"\xff\xfeUSDT_1d.parquet",  # nie-UTF-8
    ],
)
def test_odwroc_nie_rusza_nazw_poprawnych_i_obcych(nazwa):
    assert nn.odwroc_cp866(nazwa) is None


def test_symbol_z_nazwy():
    assert nn.symbol_z_nazwy("币安人生USDT_1d.parquet") == "币安人生USDT"
    assert nn.symbol_z_nazwy("币安人生USDT_funding.parquet") == "币安人生USDT"
    assert nn.symbol_z_nazwy("X_Y_oi.parquet") == "X_Y"


def _w_cp866(znak: str) -> bool:
    try:
        znak.encode("cp866")
    except UnicodeEncodeError:
        return False
    return True


@settings(max_examples=300, deadline=None)
@given(
    rdzen=st.text(
        alphabet=st.characters(
            min_codepoint=0x80, max_codepoint=0x2FFFF, exclude_categories=["Cs"]
        ),
        min_size=1,
        max_size=12,
    ),
    sufiks=st.sampled_from(["USDT_1d.parquet", "USDT_funding.parquet"]),
)
def test_wlasciwosc_odwrocenie_i_idempotencja(rdzen, sufiks):
    """Odwrócenie zawsze odtwarza bajty oryginału; nazwa ze znakiem spoza cp866 (np. CJK) nie jest
    kandydatem, więc drugi przebieg po naprawie niczego nie zmienia."""
    nazwa = rdzen + sufiks
    assert nn.odwroc_cp866(znieksztalc(nazwa)) == nazwa.encode("utf-8")
    if not all(_w_cp866(z) for z in rdzen):
        assert nn.odwroc_cp866(nazwa.encode("utf-8")) is None


# --- plan i wykonanie na sztucznym katalogu -------------------------------------------------


def test_sprawdz_tylko_plan_i_nic_nie_zmienia(katalog, ref_csv, capsys):
    przed = _stan(katalog)
    kod = nn.main(["--sprawdz", katalog, "--symbole", ref_csv])
    out = capsys.readouterr().out
    assert kod == nn.KOD_OK
    assert _stan(katalog) == przed  # nazwy, treść i czas modyfikacji bez zmian
    assert out.count("[DO_ZMIANY]") == 2 and out.count("[POPRAWNA]") == 1
    assert "nowa:            币安人生USDT_1d.parquet" in out
    assert repr(znieksztalc("币安人生USDT_1d.parquet")) in out  # stara nazwa w bajtach
    assert (
        nn.sha256_pliku(os.path.join(os.fsencode(katalog), znieksztalc("币安人生USDT_1d.parquet")))
        in out
    )


def test_wykonaj_zmienia_tylko_nazwy_i_jest_idempotentne(katalog, ref_csv, capsys):
    przed = _stan(katalog)
    assert nn.main(["--wykonaj", katalog, "--symbole", ref_csv]) == nn.KOD_OK
    po = _stan(katalog)
    mapa = {
        znieksztalc("币安人生USDT_1d.parquet"): "币安人生USDT_1d.parquet".encode("utf-8"),
        znieksztalc("币安人生USDT_funding.parquet"): "币安人生USDT_funding.parquet".encode("utf-8"),
    }
    oczekiwane = {mapa.get(n, n): v for n, v in przed.items()}
    assert po == oczekiwane  # ta sama treść i mtime pod nowymi nazwami, reszta nietknięta
    assert "sha256 treści zgodne 2/2" in capsys.readouterr().out
    # drugi przebieg: nic do zmiany, wszystkie nazwy spoza ASCII poprawne
    assert nn.main(["--wykonaj", katalog, "--symbole", ref_csv]) == nn.KOD_OK
    assert _stan(katalog) == po
    out = capsys.readouterr().out
    assert "DO_ZMIANY 0" in out and "POPRAWNA 3" in out


@pytest.mark.parametrize("ta_sama", [True, False])
def test_odmowa_gdy_cel_istnieje(katalog, ref_csv, capsys, ta_sama):
    tresc = b"swiece-binance-zycie" if ta_sama else b"inna"
    _plik(katalog, "币安人生USDT_1d.parquet".encode("utf-8"), tresc)
    przed = _stan(katalog)
    assert nn.main(["--sprawdz", katalog, "--symbole", ref_csv]) == nn.KOD_BLOKADA
    out = capsys.readouterr().out
    assert "[CEL_ISTNIEJE]" in out
    assert ("ta sama treść" if ta_sama else "INNA treść") in out
    assert nn.main(["--wykonaj", katalog, "--symbole", ref_csv]) == nn.KOD_BLOKADA
    assert _stan(katalog) == przed  # wszystko albo nic: druga (wolna) nazwa też nie zmieniona
    assert "ODMOWA" in capsys.readouterr().out


def test_odmowa_gdy_symbol_niepotwierdzony(katalog, tmp_path, capsys):
    ref = tmp_path / "ref.parquet"
    pd.DataFrame({"symbol": ["BTCUSDT"]}).to_parquet(ref)
    przed = _stan(katalog)
    assert nn.main(["--wykonaj", katalog, "--symbole", str(ref)]) == nn.KOD_BLOKADA
    out = capsys.readouterr().out
    assert out.count("[NIEPOTWIERDZONA]") == 2 and "ODMOWA" in out
    assert _stan(katalog) == przed


def test_nazwa_spoza_utf8_blokuje(katalog, ref_csv, capsys):
    _plik(katalog, b"\xff\xfeUSDT_1d.parquet", b"x")
    przed = _stan(katalog)
    assert nn.main(["--wykonaj", katalog, "--symbole", ref_csv]) == nn.KOD_BLOKADA
    assert "[NIE_UTF8]" in capsys.readouterr().out
    assert _stan(katalog) == przed


def test_katalog_zamiast_pliku_blokuje(katalog, ref_csv, capsys):
    os.mkdir(os.path.join(os.fsencode(katalog), znieksztalc("龙虾USDT")))
    assert nn.main(["--sprawdz", katalog, "--symbole", ref_csv]) == nn.KOD_BLOKADA
    assert "[NIE_PLIK]" in capsys.readouterr().out


def test_zmiana_nazwy_nigdy_nie_nadpisuje(tmp_path):
    zrodlo = _plik(tmp_path, b"a", b"stara")
    cel = _plik(tmp_path, b"b", b"cel")
    with pytest.raises(FileExistsError):
        nn.zmien_nazwe_bez_nadpisania(zrodlo, cel)
    assert open(zrodlo, "rb").read() == b"stara" and open(cel, "rb").read() == b"cel"


def test_cel_pojawia_sie_po_planie_przerywa_bez_nadpisania(katalog, ref_csv, capsys):
    """Wyścig: plan bez blokad, ale plik o nowej nazwie powstaje przed zmianą → przerwanie, bez nadpisania."""
    plan = nn.zaplanuj([katalog], nn.wczytaj_symbole([ref_csv]))
    do_zmiany = [p for p in plan if p.status == nn.DO_ZMIANY]
    assert len(do_zmiany) == 2
    pierwsza, ostatnia = do_zmiany
    _plik(katalog, ostatnia.nowa, b"obcy-plik")  # pojawia się po planie
    assert nn.wykonaj(plan) == nn.KOD_BLAD
    out = capsys.readouterr().out
    assert "PRZERWANO" in out and "wykonano 1 zmian" in out
    assert open(ostatnia.cel, "rb").read() == b"obcy-plik"  # nie nadpisany
    assert open(ostatnia.sciezka, "rb").read() == b"funding-binance-zycie"  # źródło zostaje
    assert not os.path.lexists(pierwsza.sciezka) and os.path.exists(pierwsza.cel)
    # ponowny plan pokazuje resztę jako blokadę do przeglądu
    assert nn.main(["--sprawdz", katalog, "--symbole", ref_csv]) == nn.KOD_BLOKADA
    assert "[CEL_ISTNIEJE]" in capsys.readouterr().out


def test_referencje_csv_z_bom(katalog, tmp_path, capsys):
    ref = tmp_path / "bom.csv"
    ref.write_bytes("symbol\n币安人生USDT\n".encode("utf-8-sig"))
    assert nn.main(["--sprawdz", katalog, "--symbole", str(ref)]) == nn.KOD_OK
    assert capsys.readouterr().out.count("[DO_ZMIANY]") == 2


def test_bledy_wejscia(tmp_path, ref_csv, capsys):
    assert nn.main(["--sprawdz", str(tmp_path / "brak"), "--symbole", ref_csv]) == nn.KOD_BLAD
    zly = tmp_path / "zly.csv"
    pd.DataFrame({"sym": ["X"]}).to_csv(zly, index=False)
    assert nn.main(["--sprawdz", str(tmp_path), "--symbole", str(zly)]) == nn.KOD_BLAD
    assert "brak kolumny `symbol`" in capsys.readouterr().out
    with pytest.raises(SystemExit):  # tryb obowiązkowy i wyłączny
        nn.main(["--sprawdz", "--wykonaj", str(tmp_path), "--symbole", ref_csv])
