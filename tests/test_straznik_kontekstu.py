"""Testy strażnika kontekstu (`tools/straznik_kontekstu.py`, docs/rag/12) na syntetycznym zapisie
rozmowy: progi, odczyt ogona zapisu blokami, jednorazowe znaczniki, pomijanie subagentów,
bezpieczeństwo hooka (zawsze kod 0, przy błędzie cisza) i linia statusu."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import straznik_kontekstu as sk

ROOT = Path(__file__).resolve().parents[1]
SKRYPT = ROOT / "tools" / "straznik_kontekstu.py"


def wpis_modelu(kontekst: int, *, sidechain: bool = False, model: str = "claude-opus-5-5") -> dict:
    # rozkład jak w prawdziwym zapisie: prawie cały kontekst z odczytu cache
    usage = {
        "input_tokens": 2,
        "cache_creation_input_tokens": 1000,
        "cache_read_input_tokens": kontekst - 1002,
        "output_tokens": 50,
    }
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {"model": model, "usage": usage},
    }


def wynik_narzedzia(rozmiar: int) -> dict:
    tresc = [{"type": "tool_result", "content": "x" * rozmiar}]
    return {"type": "user", "isSidechain": False, "message": {"role": "user", "content": tresc}}


def zapisz(katalog: Path, wpisy: list[dict], koncowka: str = "\n") -> Path:
    sciezka = katalog / "sesja.jsonl"
    sciezka.write_text("\n".join(json.dumps(w) for w in wpisy) + koncowka, encoding="utf-8")
    return sciezka


def zdarzenie(zapis: Path, event: str = "PostToolUse", **pola) -> str:
    dane = {"session_id": "s1", "transcript_path": str(zapis), "hook_event_name": event}
    return json.dumps({**dane, "tool_name": "Bash", **pola})


def hook_przy(tmp_path: Path, kontekst: int, event: str = "PostToolUse", **pola) -> dict:
    """Hook po wywołaniu modelu z danym kontekstem; {} = hook milczy."""
    zapis = zapisz(tmp_path, [wpis_modelu(kontekst), wynik_narzedzia(100)])
    wyjscie = sk.hook_main(zdarzenie(zapis, event, **pola), baza_stanu=tmp_path / "stan")
    return json.loads(wyjscie) if wyjscie else {}


# --- progi -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tokeny, oczekiwany",
    [(0, 0), (149_999, 0), (150_000, 1), (249_999, 1), (250_000, 2), (299_999, 2), (300_000, 3)],
)
def test_poziom_na_granicach_progow(tokeny, oczekiwany):
    assert sk.poziom(tokeny) == oczekiwany


def test_progi_sa_uporzadkowane_i_opisane_w_docs_rag_12():
    assert 0 < sk.PROG_UWAGI < sk.PROG_PRZEKAZANIA and sk.KROK_PRZYPOMNIENIA > 0
    doc = (ROOT / "docs" / "rag" / "12_zuzycie_tokenow.md").read_text(encoding="utf-8")
    for prog in (sk.PROG_UWAGI, sk.PROG_PRZEKAZANIA, sk.KROK_PRZYPOMNIENIA):
        assert f"{sk.tys(prog)} tys." in doc, prog
    assert f"co {sk.tys(sk.KROK_PRZYPOMNIENIA)} tys." in doc


# --- odczyt zapisu rozmowy --------------------------------------------------------------------


def test_kontekst_ostatniego_wywolania_przez_wiele_blokow(tmp_path):
    wpisy = [
        wpis_modelu(100_000),
        wynik_narzedzia(10),
        wpis_modelu(120_000),
        wynik_narzedzia(20_000),
    ]
    assert sk.kontekst_z_zapisu(zapisz(tmp_path, wpisy), blok=1024) == 120_000


def test_pomija_subagenta_i_wpis_syntetyczny(tmp_path):
    syntetyczny = wpis_modelu(5000, model="<synthetic>")
    wpisy = [wpis_modelu(120_000), wpis_modelu(900_000, sidechain=True), syntetyczny]
    assert sk.kontekst_z_zapisu(zapisz(tmp_path, wpisy)) == 120_000


def test_ucieta_ostatnia_linia_jest_pomijana(tmp_path):
    niepelna = json.dumps(wpis_modelu(300_000))[:-40]  # linia właśnie dopisywana
    zapis = zapisz(tmp_path, [wpis_modelu(120_000)])
    zapis.write_text(zapis.read_text(encoding="utf-8") + niepelna, encoding="utf-8")
    assert sk.kontekst_z_zapisu(zapis, blok=64) == 120_000


def test_brak_wywolan_modelu_daje_none(tmp_path):
    assert sk.kontekst_z_zapisu(tmp_path / "brak.jsonl") is None
    assert sk.kontekst_z_zapisu(zapisz(tmp_path, [], koncowka="")) is None
    assert sk.kontekst_z_zapisu(zapisz(tmp_path, [wynik_narzedzia(10)])) is None
    assert sk.kontekst_z_zapisu(tmp_path) is None  # katalog zamiast pliku


def test_odczyt_wstecz_ma_limit(tmp_path):
    zapis = zapisz(tmp_path, [wpis_modelu(120_000), wynik_narzedzia(10_000)])
    assert sk.kontekst_z_zapisu(zapis, blok=1024, maks=4096) is None
    assert sk.kontekst_z_zapisu(zapis, blok=1024, maks=64 * 1024) == 120_000


WPIS = st.one_of(
    st.integers(2_000, 900_000).map(wpis_modelu),
    st.integers(2_000, 900_000).map(lambda k: wpis_modelu(k, sidechain=True)),
    st.integers(0, 3000).map(wynik_narzedzia),
)


@settings(max_examples=60, deadline=None)
@given(wpisy=st.lists(WPIS, max_size=12), blok=st.integers(1, 5000))
def test_odczyt_blokami_rowny_pelnemu_skanowi(wpisy, blok):
    """Właściwość: dowolny rozmiar bloku daje to samo, co przejście całego pliku od początku."""
    oczekiwany = None
    for w in wpisy:
        if w["type"] == "assistant" and not w["isSidechain"]:
            oczekiwany = sk.kontekst(w["message"]["usage"])
    with tempfile.TemporaryDirectory() as katalog:
        assert sk.kontekst_z_zapisu(zapisz(Path(katalog), wpisy), blok=blok) == oczekiwany


# --- hook PostToolUse: jednorazowe znaczniki -----------------------------------------------------


def test_ponizej_progu_hook_milczy(tmp_path):
    assert hook_przy(tmp_path, 149_000) == {}


def test_uwaga_przy_progu_jest_jednorazowa(tmp_path):
    pierwsza = hook_przy(tmp_path, 160_000)
    tekst = pierwsza["hookSpecificOutput"]["additionalContext"]
    assert pierwsza["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "160 tys." in tekst and "subagent" in tekst and "systemMessage" not in pierwsza
    assert hook_przy(tmp_path, 170_000) == {}


def test_przekazanie_z_nota_i_komunikatem_dla_uzytkownika(tmp_path):
    wyjscie = hook_przy(tmp_path, 260_000)
    tekst = wyjscie["hookSpecificOutput"]["additionalContext"]
    assert "nota-przekazania.md" in tekst and "/clear" in tekst and "Nie zaczynaj" in tekst
    assert "/clear" in wyjscie["systemMessage"]


def test_przypomnienie_co_krok_ponad_progiem_przekazania(tmp_path):
    assert hook_przy(tmp_path, 260_000)
    assert hook_przy(tmp_path, 299_000) == {}
    assert "300 tys." in hook_przy(tmp_path, 300_000)["hookSpecificOutput"]["additionalContext"]


def test_skok_prosto_do_przekazania_nie_odpala_potem_zaleglej_uwagi(tmp_path):
    assert hook_przy(tmp_path, 260_000)
    assert hook_przy(tmp_path, 200_000) == {}  # np. streszczenie do 200 tys.


def test_spadek_ponizej_uwagi_uzbraja_progi_na_nowo(tmp_path):
    assert hook_przy(tmp_path, 160_000)
    assert hook_przy(tmp_path, 90_000) == {}  # streszczenie rozmowy
    assert hook_przy(tmp_path, 160_000)


def test_znaczniki_sa_osobne_dla_kazdej_sesji(tmp_path):
    assert hook_przy(tmp_path, 160_000, session_id="a")
    assert hook_przy(tmp_path, 160_000, session_id="b")


def test_narzedzie_subagenta_jest_pomijane(tmp_path):
    assert hook_przy(tmp_path, 260_000, agent_id="a123", agent_type="lokalizator") == {}
    assert not (tmp_path / "stan").exists()


# --- hook UserPromptSubmit --------------------------------------------------------------------


def test_przypomnienie_na_starcie_tury_przy_kazdym_poleceniu(tmp_path):
    assert hook_przy(tmp_path, 100_000, "UserPromptSubmit") == {}
    for _ in range(2):
        wyjscie = hook_przy(tmp_path, 160_000, "UserPromptSubmit")
        assert wyjscie["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "nową sesję" in wyjscie["hookSpecificOutput"]["additionalContext"]
    ponad = hook_przy(tmp_path, 260_000, "UserPromptSubmit")["hookSpecificOutput"]
    assert "progiem przekazania" in ponad["additionalContext"]
    assert not (tmp_path / "stan").exists()  # start tury nie zużywa jednorazowych znaczników


# --- bezpieczeństwo hooka ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "surowe",
    [
        b"",
        b"to nie json",
        b"[]",
        b"\xff\xfe\x00",
        json.dumps({"hook_event_name": "PostToolUse"}).encode(),
        json.dumps({"hook_event_name": "Stop", "transcript_path": "x"}).encode(),
        json.dumps({"hook_event_name": "PostToolUse", "transcript_path": 7}).encode(),
    ],
)
def test_hook_przy_zlych_danych_milczy(surowe, tmp_path):
    assert sk.hook_main(surowe, baza_stanu=tmp_path) == ""


def test_hook_milczy_gdy_katalog_stanu_niedostepny(tmp_path):
    zapis = zapisz(tmp_path, [wpis_modelu(160_000)])
    zajety = tmp_path / "plik"
    zajety.write_text("to plik, nie katalog", encoding="utf-8")
    assert sk.hook_main(zdarzenie(zapis), baza_stanu=zajety) == ""


@pytest.mark.parametrize("wejscie_ok", [True, False])
def test_skrypt_hooka_konczy_sie_kodem_0(tmp_path, wejscie_ok):
    zapis = zapisz(tmp_path, [wpis_modelu(160_000)])
    wejscie = zdarzenie(zapis) if wejscie_ok else "zepsute {"
    temp = {zmienna: str(tmp_path) for zmienna in ("TMPDIR", "TEMP", "TMP")}  # znaczniki w tmp_path
    wynik = subprocess.run(
        [sys.executable, str(SKRYPT), "hook"],
        input=wejscie.encode(),
        capture_output=True,
        timeout=30,
        env={**os.environ, **temp},
    )
    assert wynik.returncode == 0
    if wejscie_ok:
        wynik.stdout.decode("ascii")  # JSON w ASCII: bez kłopotu ze stroną kodową Windows
        assert json.loads(wynik.stdout)["hookSpecificOutput"]["additionalContext"]
        assert (tmp_path / "clas5-straznik" / "s1" / "poziom-1").exists()
    else:
        assert wynik.stdout == b""


# --- linia statusu ----------------------------------------------------------------------------


def test_status_z_okna_kontekstu_claude_code():
    dane = {
        "model": {"id": "claude-opus-5-5", "display_name": "Opus 5.5"},
        "effort": {"level": "max"},
        "context_window": {
            "current_usage": {
                "input_tokens": 2,
                "output_tokens": 2,
                "cache_creation_input_tokens": 814,
                "cache_read_input_tokens": 164_420,
            }
        },
    }
    linia = sk.linia_statusu(json.dumps(dane))
    assert linia.startswith("Opus 5.5 (max) · ")
    assert "kontekst 165 tys." in linia and "domknij etap" in linia and sk.KOLORY[1] in linia


def test_status_z_zapisu_gdy_brak_okna_kontekstu(tmp_path):
    zapis = zapisz(tmp_path, [wpis_modelu(260_000)])
    linia = sk.linia_statusu(json.dumps({"transcript_path": str(zapis)}))
    assert "kontekst 260 tys." in linia and "/clear" in linia and sk.KOLORY[2] in linia


@pytest.mark.parametrize("surowe", [b"", b"zepsute", b"[]", b'{"model": "x", "context_window": 5}'])
def test_status_bez_danych(surowe):
    assert sk.linia_statusu(surowe).endswith("kontekst —")


def test_status_z_modelem_jako_tekstem():
    linia = sk.linia_statusu(json.dumps({"model": "claude-opus-5-5"}))
    assert linia == "claude-opus-5-5 · kontekst —"


def test_skrypt_statusu_drukuje_linie():
    dane = {"context_window": {"current_usage": {"cache_read_input_tokens": 72_000}}}
    wynik = subprocess.run(
        [sys.executable, str(SKRYPT), "status"],
        input=json.dumps(dane).encode(),
        capture_output=True,
        timeout=30,
    )
    assert wynik.returncode == 0 and "kontekst 72 tys." in wynik.stdout.decode("utf-8")
