"""zuzycie_tokenow.py — ile tokenów zużywa praca Claude Code nad projektem i na co (monitor, tylko odczyt).

Po co (prośba użytkownika 2026-09-28: „monitorować zużycie i optymalizować bez utraty jakości”): pomiar
PRZED jakąkolwiek optymalizacją. Pierwszy pomiar (docs/rag/12) pokazał, że koszt nie siedzi tam, gdzie
podejrzewano (wyjścia narzędzi), tylko w długości głównej sesji, przepisaniach kontekstu po przerwie
i workflow wieloagentowych.

Źródło: zapisy rozmów Claude Code na tej maszynie — `~/.claude/projects/<katalog projektu>/*.jsonl`
(główne sesje) i podkatalogi `<sesja>/subagents/` (subagenci) oraz `<sesja>/subagents/workflows/<id>/`
(workflow). Niczego nie zapisuje. Inne maszyny (Windows, Cowork) mają własne zapisy — tu ich nie ma.

Zasady liczenia:
- jedna odpowiedź modelu bywa zapisana w kilku rekordach (bloki treści, zapis przed końcem strumienia)
  z tym samym `message.id` — scalamy je, biorąc NAJWIĘKSZĄ wartość każdego licznika (pierwszy rekord
  potrafi mieć wyjście 1 zamiast pełnego);
- koszt w USD = liczniki wywołania × cena katalogowa JEGO modelu (CENNIK_USD_ZA_MLN — jedyne miejsce cen,
  z datą cennika): wejście, zapis cache 5 min, zapis cache 1 h, odczyt cache, wyjście. Model spoza cennika
  ma koszt USD nieznany: raport podaje go osobno (wywołania i tokeny), nigdy jako 0; wpisy <synthetic> = 0;
- koszt ważony w „jednostkach wejścia” (dawna miara — zostaje dla ciągłości historii i strony) = te same
  wagi dla każdego modelu: wejście 1, zapis cache 5 min 1,25, zapis cache 1 h 2, odczyt cache 0,1,
  wyjście 5. Zawyża koszt czytania kontekstu (odczyt Opusa 5.5 to 0,05 ceny wejścia, Fable 5.1 — 0,025),
  a zaniża zapisy i wyjście — koszty porównuje się w USD (docs/rag/12, T1 i T8);
- kontekst wywołania = wejście + zapis + odczyt cache (tyle model „przeczytał” w tym wywołaniu);
- przepisanie kontekstu = wywołanie z zapisem ≥ 200 tys. przy odczycie < 50 tys. (cache wygasł po
  przerwie > 1 h albo po streszczeniu rozmowy) — cały kontekst zapisany od nowa po podwójnej cenie.

    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py                 # cały zapis tego projektu
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --od 2026-09-27 # od dnia (UTC)
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --json          # dane do dalszej obróbki
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --stan runs/tokeny/stan.json  # dane strony „Tokeny CLAS-5”
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --progi         # symulacja progów strażnika kontekstu
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --progi --jednostki  # ta sama symulacja w dawnych jednostkach

Strona „Tokeny CLAS-5” (docs/rag/12) czyta dokument bazy zbudowany przez `--stan`: wiersz na dzień
z podziałem na modele i źródła (jednostki; od T8 obok klucze `usd` i `usd_z` w USD), kontekstem
i przepisaniami głównej sesji oraz liczbą sesji. Plik stanu jest zarazem historią: Claude Code kasuje
zapisy rozmów po 30 dniach (`cleanupPeriodDays`), więc dni starsze niż FREEZE_DAYS zostają w pliku
takie, jak policzono je ostatnio (bez kluczy USD, jeśli policzono je przed T8), zamiast znikać.

Symulacja progów (`--progi`) sprawdza na danych progi strażnika kontekstu (`tools/straznik_kontekstu.py`):
co by było, gdyby główną sesję czyścić (/clear + nota przekazania) zawsze, gdy jej kontekst przekroczy
próg X. Nowa sesja zaczyna z kontekstem R i jednorazowym kosztem K — oba zmierzone na początkach
prawdziwych sesji (mediana). Koszt i oszczędność w USD po cenie modelu każdego wywołania (`--jednostki`
= dawne jednostki). Symulacja idzie po łańcuchu rozmowy (`parentUuid`), nie po czasie: drugi strumień
zapytań w tym samym pliku sesji (np. druga kopia rozmowy wznowiona z wcześniejszego miejsca) i gałąź po
cofnięciu rozmowy biorą stan od swojego poprzednika, a spadek kontekstu przy przełączeniu modelu (Opus ↔
Fable: bloki rozumowania drugiego modelu wypadają z kontekstu) nie jest streszczeniem. Sesje z wywołaniem
w ostatnich 60 min są pomijane (mogą jeszcze trwać). To przybliżenie: zakłada, że po czyszczeniu praca
biegnie tak samo, tylko na krótszym kontekście.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WEIGHTS = {"inp": 1.0, "cw5": 1.25, "cw1h": 2.0, "cr": 0.1, "out": 5.0}
# Cennik katalogowy API — JEDYNE miejsce cen w module (docs/rag/12, T1 i T8). USD za mln tokenów
# w kolejności liczników WEIGHTS: wejście, zapis cache 5 min, zapis cache 1 h, odczyt cache, wyjście.
# Klucz = identyfikator modelu z zapisów rozmów; pasuje też z sufiksem daty (claude-haiku-4-5-20251001)
# i okna kontekstu ([1m]). Nowy cennik = nowe ceny i nowa data, nigdy ciche nadpisanie.
CENNIK_DATA = "2026-09-28"
CENNIK_ZRODLO = "platform.claude.com/docs/en/about-claude/pricing"
CENNIK_USD_ZA_MLN: dict[str, tuple[float, float, float, float, float]] = {
    "claude-opus-5-5": (4.0, 5.0, 8.0, 0.20, 20.0),  # odczyt = 0,05 ceny wejścia
    "claude-fable-5-1": (10.0, 12.5, 20.0, 0.25, 50.0),  # odczyt = 0,025 ceny wejścia
    "claude-sonnet-5": (2.0, 2.5, 4.0, 0.20, 10.0),
    "claude-haiku-4-5": (1.0, 1.25, 2.0, 0.10, 5.0),
}
_MODEL_Z_SUFIKSEM = re.compile(r"(.+?)(?:[-@]\d{8})?(?:\[[^\]]*\])?")
REWRITE_MIN_WRITE = 200_000
REWRITE_MAX_READ = 50_000
MAIN = "główna sesja"
SUB = "subagent"
SKILL_MARK = "Base directory for this skill"
SYNTHETIC = "<synthetic>"  # wpisy harnessu bez wywołania modelu (zero tokenów) — poza stroną
GROUP_KEY = {
    MAIN: "main",
    SUB: "sub",
    "workflow": "wf",
}  # krótkie klucze źródeł w dokumencie strony
MODEL_COLS = ["koszt", "wywolan", "wejscie", "zapis_cache", "odczyt_cache", "wyjscie"]
FREEZE_DAYS = 14  # dni starszych nie przeliczamy — część ich zapisów mogła już zniknąć (30 dni)
DOC_LIMIT = 240_000  # bajtów; dokument bazy strony ma limit 256 KiB — nadmiar = najstarsze dni
# Symulacja progów (--progi). 150 i 250 tys. to PROG_UWAGI i PROG_PRZEKAZANIA z tools/straznik_kontekstu.py
# — bez importu, bo ten moduł ma działać sam (zgodność wartości pilnuje test).
PROGI_SYMULACJI = (150_000, 200_000, 250_000, 300_000, 400_000)
MNOZNIKI_K = (0.5, 1.0, 2.0)  # koszt startu nowej sesji jest niepewny: połowa, tyle samo, dwa razy
MIN_WYWOLAN_SESJI = 12  # krótsza sesja nie ma czego czyścić ani początku do zmierzenia
N_NOWEJ_SESJI = 10  # w tylu wywołaniach nowa sesja wczytuje to, czego potrzebuje do pracy
SPADEK_STRESZCZENIA = 20_000  # większy spadek kontekstu = streszczenie rozmowy albo nowy początek
PROG_SZCZEGOLOW = 250_000  # dla tego progu raport podaje liczby per sesja (w --json)
SESJA_OTWARTA = timedelta(minutes=60)  # sesja z wywołaniem tak niedawno może trwać — poza symulacją
PLASKO_PKT = 5.0  # płaski odcinek krzywej: do tylu pkt proc. od najlepszego progu (reguła T2)
# poprzednik wywołania, które otwiera łańcuch rozmowy (start sesji, wznowienie po streszczeniu)
POCZATEK = "<początek>"


def project_dir(cwd: str | Path, home: Path | None = None) -> Path:
    """Katalog zapisów Claude Code dla projektu: znaki spoza [A-Za-z0-9] w ścieżce → „-”."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve()))
    return (home or Path.home()) / ".claude" / "projects" / slug


def source_of(path: Path, root: Path) -> str:
    """Główna sesja / subagent / workflow:<id> — z położenia pliku względem katalogu projektu."""
    parts = path.relative_to(root).parts
    if "workflows" in parts:
        i = parts.index("workflows")
        return "workflow:" + (parts[i + 1] if i + 1 < len(parts) - 1 else "?")
    if "subagents" in parts:
        return SUB
    return MAIN


def _usage_counts(u: dict) -> collections.Counter:
    cc = u.get("cache_creation") or {}
    c = collections.Counter(
        inp=int(u.get("input_tokens") or 0),
        cw5=int(cc.get("ephemeral_5m_input_tokens") or 0),
        cw1h=int(cc.get("ephemeral_1h_input_tokens") or 0),
        cr=int(u.get("cache_read_input_tokens") or 0),
        out=int(u.get("output_tokens") or 0),
    )
    if not cc:  # starszy zapis bez podziału na TTL — traktujemy jak 5 min
        c["cw5"] = int(u.get("cache_creation_input_tokens") or 0)
    return c


def cost(c: collections.Counter) -> float:
    return sum(c[k] * w for k, w in WEIGHTS.items())


def cennik_modelu(model: str) -> tuple[float, ...] | None:
    """Ceny modelu z CENNIK_USD_ZA_MLN (USD za mln tokenów, kolejność liczników WEIGHTS) — po
    identyfikatorze, także z sufiksem daty albo okna kontekstu. Wpis <synthetic> harnessu = zera;
    model spoza cennika (także „?” — rekord bez pola model) = None: koszt nieznany, nie zero."""
    if model == SYNTHETIC:
        return (0.0,) * len(WEIGHTS)
    m = _MODEL_Z_SUFIKSEM.fullmatch(model)
    return CENNIK_USD_ZA_MLN.get(m.group(1)) if m else None


def ceny_tokenu(model: str, jednostki: bool = False) -> dict[str, float] | None:
    """Cena JEDNEGO tokenu każdego licznika: USD według cennika modelu albo — `jednostki` — wagi
    WEIGHTS, te same dla każdego modelu. Model spoza cennika (tylko USD) = None."""
    if jednostki:
        return WEIGHTS
    ceny = cennik_modelu(model)
    return None if ceny is None else {k: c / 1e6 for k, c in zip(WEIGHTS, ceny, strict=True)}


def koszt_usd(c: collections.Counter, model: str) -> float | None:
    """Koszt wywołania w USD po cenie katalogowej modelu; None = modelu nie ma w cenniku. Liczone
    w całych centach za mln tokenów i dzielone raz, więc wynik zgadza się co do cyfry z rachunkiem
    cennika (`total_cost_usd` z `claude -p`)."""
    ceny = cennik_modelu(model)
    if ceny is None:
        return None
    return sum(c[k] * round(100 * cena) for k, cena in zip(WEIGHTS, ceny, strict=True)) / 1e8


def context_size(c: collections.Counter) -> int:
    return c["inp"] + c["cw5"] + c["cw1h"] + c["cr"]


@dataclass
class Call:
    day: str
    source: str
    ts: str
    counts: collections.Counter
    model: str = "?"
    session: str = ""
    klucz: str = ""  # identyfikator wywołania w pliku (message.id)
    # klucz poprzednika w łańcuchu rozmowy (parentUuid); POCZATEK = wywołanie otwiera łańcuch
    # (start sesji, wznowienie po streszczeniu); "" = nieznany — wtedy poprzednie wywołanie w czasie
    poprzednik: str = ""

    @property
    def usd(self) -> float | None:
        """Koszt w USD po cenie modelu; None = model spoza cennika."""
        return koszt_usd(self.counts, self.model)

    @property
    def is_rewrite(self) -> bool:
        write = self.counts["cw5"] + self.counts["cw1h"]
        return write >= REWRITE_MIN_WRITE and self.counts["cr"] < REWRITE_MAX_READ


@dataclass
class Scan:
    calls: list[Call] = field(default_factory=list)
    skills: collections.Counter = field(default_factory=collections.Counter)
    content: collections.Counter = field(default_factory=collections.Counter)
    bad_lines: int = 0
    files: int = 0


def _len(x) -> int:
    return len(x) if isinstance(x, str) else len(json.dumps(x, ensure_ascii=False))


def _poprzednicy(
    pierwszy_rodzic: dict[str, str | None],
    rodzic: dict[str, str | None],
    wywolanie_rekordu: dict[str, str],
) -> dict[str, str]:
    """Poprzednik każdego wywołania w łańcuchu rozmowy: od rodzica pierwszego rekordu wywołania w górę
    po `parentUuid` (przez wiadomości, wyniki narzędzi, załączniki i wpisy <synthetic>) do rekordu
    INNEGO wywołania. Koniec łańcucha (parentUuid null: start sesji, granica streszczenia) = POCZATEK;
    rodzic spoza pliku, brak pól łańcucha albo pętla = "" (nieznany)."""
    out = {}
    for key, u in pierwszy_rodzic.items():
        widziane: set[str] = set()
        while True:
            if u is None:
                out[key] = POCZATEK
                break
            k = wywolanie_rekordu.get(u)
            if k is not None and k != key:
                out[key] = k
                break
            if not u or u in widziane or u not in rodzic:
                out[key] = ""
                break
            widziane.add(u)
            u = rodzic[u]
    return out


def scan_file(path: Path, source: str, scan: Scan, since: str = "") -> None:
    """Wywołania modelu z jednego pliku (scalone po message.id, z poprzednikiem w łańcuchu rozmowy)
    + dla głównej sesji: skille i treść."""
    merged: dict[str, Call] = {}
    tool_names: dict[str, str] = {}
    rodzic: dict[str, str | None] = {}  # uuid rekordu → parentUuid ("" = rekord bez pola)
    pierwszy_rodzic: dict[str, str | None] = {}  # klucz wywołania → rodzic jego pierwszego rekordu
    # uuid rekordu odpowiedzi → klucz wywołania (bez wpisów <synthetic>)
    wywolanie_rekordu: dict[str, str] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                scan.bad_lines += 1
                continue
            if not isinstance(o, dict):
                scan.bad_lines += 1
                continue
            day = str(o.get("timestamp") or "")[:10]
            if since and day and day < since:
                continue
            uid = o.get("uuid")
            if isinstance(uid, str):
                par = o.get("parentUuid", "")
                rodzic[uid] = par if par is None or isinstance(par, str) else ""
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = msg.get("content")
            if o.get("type") == "assistant":
                u = msg.get("usage")
                if isinstance(u, dict):
                    key = str(msg.get("id") or o.get("requestId") or o.get("uuid"))
                    c = _usage_counts(u)
                    prev = merged.get(key)
                    if prev is None:
                        prev = merged[key] = Call(
                            day,
                            source,
                            str(o.get("timestamp") or ""),
                            c,
                            str(msg.get("model") or "?"),
                            path.stem,
                            key,
                        )
                        pierwszy_rodzic[key] = rodzic.get(uid, "") if isinstance(uid, str) else ""
                    else:
                        prev.counts = collections.Counter(
                            {k: max(prev.counts[k], c[k]) for k in set(prev.counts) | set(c)}
                        )
                    if isinstance(uid, str) and prev.model != SYNTHETIC:
                        wywolanie_rekordu[uid] = key
                if source == MAIN and isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_use":
                            tool_names[str(b.get("id"))] = str(b.get("name"))
                            scan.content["asystent: argumenty narzędzi"] += _len(b.get("input"))
                            if b.get("name") == "Skill" and isinstance(b.get("input"), dict):
                                scan.skills[str(b["input"].get("skill"))] += 1
                        elif b.get("type") == "text":
                            scan.content["asystent: tekst"] += _len(b.get("text", ""))
            elif o.get("type") == "user" and source == MAIN:
                blocks = [content] if isinstance(content, str) else content or []
                for b in blocks:
                    if isinstance(b, str):
                        key = "skille" if SKILL_MARK in b else "wiadomości użytkownika/systemu"
                        scan.content[key] += len(b)
                    elif isinstance(b, dict) and b.get("type") == "tool_result":
                        name = tool_names.get(str(b.get("tool_use_id")), "?")
                        name = name if name in ("Bash", "Read") else "inne narzędzia"
                        cc = b.get("content")
                        n = (
                            sum(_len(x.get("text", "")) for x in cc if isinstance(x, dict))
                            if isinstance(cc, list)
                            else _len(cc)
                        )
                        scan.content["wyniki: " + name] += n
                    elif isinstance(b, dict) and b.get("type") == "text":
                        t = b.get("text", "")
                        key = "skille" if SKILL_MARK in t else "wiadomości użytkownika/systemu"
                        scan.content[key] += len(t)
            elif o.get("type") == "attachment" and source == MAIN:
                a = o.get("attachment")
                kind = a.get("type") if isinstance(a, dict) else None
                if kind == "invoked_skills":
                    scan.content["skille"] += _len(a)
                elif kind != "prompt_snapshot":  # zapis diagnostyczny harnessu, nie nowa treść
                    scan.content["przypomnienia i załączniki"] += _len(a)
    for key, pop in _poprzednicy(pierwszy_rodzic, rodzic, wywolanie_rekordu).items():
        merged[key].poprzednik = pop
    scan.calls.extend(merged.values())
    scan.files += 1


def scan_project(root: Path, since: str = "") -> Scan:
    scan = Scan()
    if not root.is_dir():
        return scan
    for path in sorted(root.rglob("*.jsonl")):
        if "memory" in path.relative_to(root).parts:
            continue
        scan_file(path, source_of(path, root), scan, since)
    return scan


def summarize(scan: Scan) -> dict:
    """Liczby do raportu: dzień × grupa źródeł, źródła, modele, konteksty, przepisania, skille, treść.
    Koszt dwiema miarami: `usd` po cenie modelu (wywołania modeli spoza cennika poza sumą — osobno
    w `bez_ceny`, z tokenami w wierszach modeli) i dawne jednostki `koszt`."""
    by_day: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    by_src: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_model: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    ctx: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
    rewrites = []
    for call in scan.calls:
        group = "workflow" if call.source.startswith("workflow:") else call.source
        c = collections.Counter(call.counts)
        c["calls"] = 1
        c["koszt"] = cost(call.counts)
        usd = call.usd
        if usd is None:
            c["bez_ceny"] = 1
        else:
            c["usd"] = usd
        by_day[(call.day, group)] += c
        by_src[call.source] += c
        by_model[call.model] += c
        ctx[(call.day, group)].append(context_size(call.counts))
        if call.source == MAIN and call.is_rewrite:
            rewrites.append(
                {
                    "ts": call.ts,
                    "zapis": call.counts["cw5"] + call.counts["cw1h"],
                    "koszt": cost(call.counts),
                    "usd": usd,
                }
            )
    total = sum((cost(c.counts) for c in scan.calls), 0.0)
    bez_ceny = sorted(m for m in by_model if cennik_modelu(m) is None)
    return {
        "razem_koszt": total,
        "razem_usd": sum(c["usd"] for c in by_model.values()),
        "razem_wywolan": len(scan.calls),
        "cennik": {"data": CENNIK_DATA, "zrodlo": CENNIK_ZRODLO},
        "bez_ceny": {"wywolan": sum(by_model[m]["calls"] for m in bez_ceny), "modele": bez_ceny},
        "dni": [
            {
                "dzien": d,
                "zrodlo": g,
                "wywolan": c["calls"],
                "wejscie": c["inp"],
                "zapis_cache": c["cw5"] + c["cw1h"],
                "odczyt_cache": c["cr"],
                "wyjscie": c["out"],
                "koszt": c["koszt"],
                "usd": c["usd"],
                "kontekst_mediana": int(statistics.median(ctx[(d, g)])),
                "kontekst_max": max(ctx[(d, g)]),
            }
            for (d, g), c in sorted(by_day.items())
        ],
        "zrodla": sorted(
            (
                {
                    "zrodlo": s,
                    "wywolan": c["calls"],
                    "koszt": c["koszt"],
                    "usd": c["usd"],
                    "wywolan_bez_ceny": c["bez_ceny"],
                }
                for s, c in by_src.items()
            ),
            key=lambda r: (-r["usd"], -r["koszt"]),
        ),
        "przepisania": sorted(rewrites, key=lambda r: r["ts"]),
        "skille": dict(scan.skills.most_common()),
        "tresc_glownej_sesji_znaki": dict(scan.content.most_common()),
        "modele": sorted(
            (
                {
                    "model": m,
                    "wywolan": c["calls"],
                    "wejscie": c["inp"],
                    "zapis_cache": c["cw5"] + c["cw1h"],
                    "odczyt_cache": c["cr"],
                    "wyjscie": c["out"],
                    "koszt": c["koszt"],
                    "usd": None if m in bez_ceny else c["usd"],
                }
                for m, c in by_model.items()
            ),
            key=lambda r: (-(r["usd"] or 0.0), -r["koszt"]),
        ),
        "zle_linie": scan.bad_lines,
        "pliki": scan.files,
    }


def day_rows(scan: Scan) -> dict[str, dict]:
    """Wiersz na dzień dla strony: modele [MODEL_COLS], źródła [koszt, wywołań], kontekst głównej
    sesji [mediana, maks.], przepisania [liczba, koszt] i liczba głównych sesji z wywołaniem tego dnia
    (tablice w jednostkach — bez zmian od wersji 1). NOWE klucze (T8): `usd` = {model: USD po cenie
    modelu albo null, gdy modelu nie ma w cenniku} i `usd_z` = {źródło: USD wywołań z ceną}.
    """
    rows: dict[str, dict] = {}
    ctx: dict[str, list[int]] = collections.defaultdict(list)
    sessions: dict[str, set[str]] = collections.defaultdict(set)
    for call in scan.calls:
        if not call.day or call.model == SYNTHETIC:
            continue
        r = rows.setdefault(
            call.day,
            {
                "d": call.day,
                "m": {},
                "z": {},
                "ctx": [0, 0],
                "prz": [0, 0],
                "ses": 0,
                "usd": {},
                "usd_z": {},
            },
        )
        c, k, usd = call.counts, cost(call.counts), call.usd
        r["usd"][call.model] = None if usd is None else r["usd"].get(call.model, 0.0) + usd
        m = r["m"].setdefault(call.model, [0.0] + [0] * (len(MODEL_COLS) - 1))
        for i, v in enumerate((k, 1, c["inp"], c["cw5"] + c["cw1h"], c["cr"], c["out"])):
            m[i] += v
        group = "workflow" if call.source.startswith("workflow:") else call.source
        z = r["z"].setdefault(GROUP_KEY[group], [0.0, 0])
        z[0] += k
        z[1] += 1
        r["usd_z"][GROUP_KEY[group]] = r["usd_z"].get(GROUP_KEY[group], 0.0) + (usd or 0.0)
        if call.source == MAIN:
            ctx[call.day].append(context_size(c))
            sessions[call.day].add(call.session)
            if call.is_rewrite:
                r["prz"][0] += 1
                r["prz"][1] += k
    for d, r in rows.items():
        for v in (*r["m"].values(), *r["z"].values(), r["prz"]):
            v[0] = round(v[0]) if isinstance(v[0], float) else v[0]
        r["prz"][1] = round(r["prz"][1])
        r["usd"] = {m: None if v is None else round(v, 4) for m, v in r["usd"].items()}
        r["usd_z"] = {g: round(v, 4) for g, v in r["usd_z"].items()}
        if ctx[d]:
            r["ctx"] = [int(statistics.median(ctx[d])), max(ctx[d])]
        r["ses"] = len(sessions[d])
    return rows


def merge_days(old: list[dict], new: dict[str, dict], today: str) -> list[dict]:
    """Historia + świeże przeliczenie: dzień z ostatnich FREEZE_DAYS (albo nieznany historii) bierze
    wartość świeżą, starszy zostaje z historii — jego zapisy mogły już zostać skasowane."""
    cutoff = (date.fromisoformat(today) - timedelta(days=FREEZE_DAYS)).isoformat()
    out = {r["d"]: r for r in old}
    for d, r in new.items():
        if d >= cutoff or d not in out:
            out[d] = r
    return [out[d] for d in sorted(out)]


def write_state(
    path: Path, scan: Scan, now: datetime | None = None, limit: int = DOC_LIMIT
) -> dict:
    """Dokument strony „Tokeny CLAS-5”: scala plik `path` (historia) ze świeżym skanem, przycina
    najstarsze dni do `limit` bajtów i zapisuje atomowo. Uszkodzony plik historii = błąd, nie reset.
    """
    now = now or datetime.now(timezone.utc)
    old = json.loads(path.read_text(encoding="utf-8"))["dni"] if path.exists() else []
    state = {
        "wersja": 1,
        "wygenerowano": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zrodlo": "zapisy Claude Code projektu alpha na serwerze Linux (bez Windows i Cowork)",
        "kolumny_modelu": MODEL_COLS,
        "kolumny_zrodla": ["koszt", "wywolan"],
        "cennik": {  # nowy klucz (T8): ceny, po których liczone są klucze `usd` i `usd_z` dni
            "data": CENNIK_DATA,
            "zrodlo": CENNIK_ZRODLO,
            "kolumny": ["wejscie", "zapis_5m", "zapis_1h", "odczyt", "wyjscie"],
            "usd_za_mln": {m: list(p) for m, p in CENNIK_USD_ZA_MLN.items()},
        },
        "dni": merge_days(old, day_rows(scan), now.date().isoformat()),
    }
    while len(state["dni"]) > 1 and len(json.dumps(state, ensure_ascii=False).encode()) > limit:
        state["dni"].pop(0)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)
    return state


def report(s: dict) -> str:
    """Raport tekstowy: koszt w USD po cenie modelu i w milionach dawnych jednostek (M)."""
    tot, tot_usd = s["razem_koszt"] or 1.0, s["razem_usd"] or 1.0
    bc = s["bez_ceny"]
    out = [
        f"ZUŻYCIE TOKENÓW — plików {s['pliki']}, wywołań modelu {s['razem_wywolan']} "
        f"(złe linie {s['zle_linie']})",
        f"Koszt według cennika API z {s['cennik']['data']}: {s['razem_usd']:.2f} USD; koszt ważony "
        f"(dawna miara, ta sama dla każdego modelu): {s['razem_koszt'] / 1e6:.1f} M jednostek wejścia",
    ]
    if bc["wywolan"]:
        out.append(
            f"UWAGA: {bc['wywolan']} wywołań modeli spoza cennika ({', '.join(bc['modele'])}) — ich "
            "koszt USD jest nieznany i nie wchodzi do sum USD (tokeny: wiersze modeli niżej)."
        )
    out += [
        "",
        f"{'dzień':10} {'źródło':13} {'wywołań':>7} {'zapis cache':>12} {'odczyt cache':>13} "
        f"{'wyjście':>9} {'koszt M':>8} {'USD':>8} {'kontekst med./max (tys.)':>25}",
    ]
    for r in s["dni"]:
        out.append(
            f"{r['dzien']:10} {r['zrodlo']:13} {r['wywolan']:7d} {r['zapis_cache']:12,d} "
            f"{r['odczyt_cache']:13,d} {r['wyjscie']:9,d} {r['koszt'] / 1e6:8.2f} {r['usd']:8.2f} "
            f"{r['kontekst_mediana'] / 1e3:14.0f} / {r['kontekst_max'] / 1e3:5.0f}"
        )
    out += ["", "Źródła (od największego kosztu w USD; obok dawne jednostki):"]
    for r in s["zrodla"]:
        out.append(
            f"  {r['zrodlo']:32} {r['usd']:9.2f} USD ({100 * r['usd'] / tot_usd:4.1f} %) "
            f"{r['koszt'] / 1e6:8.2f} M ({100 * r['koszt'] / tot:4.1f} %), wywołań {r['wywolan']}"
            + (f", w tym bez ceny {r['wywolan_bez_ceny']}" if r["wywolan_bez_ceny"] else "")
        )
    out += [
        "",
        "Modele (USD — cena katalogowa modelu; jednostki — ta sama waga dla każdego modelu, więc "
        "zawyżają udział tanich modeli):",
    ]
    for r in s["modele"]:
        usd = (
            f"{r['usd']:9.2f} USD ({100 * r['usd'] / tot_usd:4.1f} %)"
            if r["usd"] is not None
            else f"USD nieznany — brak w cenniku; wejście {r['wejscie']:,d}, zapis cache "
            f"{r['zapis_cache']:,d}, odczyt cache {r['odczyt_cache']:,d}, wyjście {r['wyjscie']:,d};"
        )
        out.append(
            f"  {r['model']:32} {usd} {r['koszt'] / 1e6:8.2f} M ({100 * r['koszt'] / tot:4.1f} %), "
            f"wywołań {r['wywolan']}"
        )
    rw = s["przepisania"]
    rw_cost = sum(r["koszt"] for r in rw)
    rw_usd = sum(r["usd"] or 0.0 for r in rw)
    out += [
        "",
        f"Przepisania całego kontekstu głównej sesji (cache wygasł po przerwie > 1 h lub po "
        f"streszczeniu): {len(rw)}, koszt {rw_usd:.2f} USD ({100 * rw_usd / tot_usd:.1f} %), "
        f"{rw_cost / 1e6:.2f} M ({100 * rw_cost / tot:.1f} %)",
    ]
    for r in rw[-10:]:
        usd = "USD nieznany" if r["usd"] is None else f"{r['usd']:.2f} USD"
        out.append(
            f"  {r['ts'][:16]}  zapis {r['zapis'] / 1e3:5.0f} tys.  koszt {usd}, "
            f"{r['koszt'] / 1e6:.2f} M"
        )
    out += ["", "Wczytania skilli w głównej sesji (każde dokłada pełną treść skilla do kontekstu):"]
    out.append(
        "  " + ", ".join(f"{k} ×{v}" for k, v in s["skille"].items()) if s["skille"] else "  brak"
    )
    ct = s["tresc_glownej_sesji_znaki"]
    ctot = sum(ct.values()) or 1
    out += [
        "",
        "Treść dodana do kontekstu głównej sesji (znaki; bez rozumowania modelu, które nie trafia do zapisu):",
    ]
    for k, v in ct.items():
        out.append(f"  {k:40} {v:12,d}  {100 * v / ctot:5.1f} %")
    return "\n".join(out)


def sesje_glowne(scan: Scan, min_wywolan: int = MIN_WYWOLAN_SESJI) -> list[list[Call]]:
    """Wywołania głównej sesji (bez wpisów <synthetic>) pogrupowane po sesji, każda posortowana po
    czasie. Zostają sesje z co najmniej `min_wywolan` wywołaniami, od najwcześniej zaczętej."""
    by_session: dict[str, list[Call]] = collections.defaultdict(list)
    for call in scan.calls:
        if call.source == MAIN and call.model != SYNTHETIC:
            by_session[call.session].append(call)
    sesje = [sorted(cs, key=lambda c: c.ts) for cs in by_session.values() if len(cs) >= min_wywolan]
    return sorted(sesje, key=lambda cs: (cs[0].ts, cs[0].session))


def _koszt_wywolania(call: Call, jednostki: bool) -> float | None:
    """Koszt wywołania w mierze symulacji: dawne jednostki albo USD (None = model spoza cennika)."""
    return cost(call.counts) if jednostki else call.usd


def _suma_kosztow(calls: list[Call], jednostki: bool) -> float:
    """Suma kosztów wywołań. Wywołanie modelu spoza cennika wnosi 0 — raport progów podaje liczbę
    takich wywołań osobno (`wywolan_bez_ceny`), więc to nie jest ciche zero."""
    return sum((_koszt_wywolania(c, jednostki) or 0.0 for c in calls), 0.0)


def parametry_nowej_sesji(
    sesje: list[list[Call]], n: int = N_NOWEJ_SESJI, jednostki: bool = False
) -> dict:
    """Start od nowa zmierzony na początkach prawdziwych sesji (mediana, żeby jedna nietypowa sesja
    nie przesuwała wyniku; obok zakres):
    - R = kontekst n-tego wywołania: tyle czyta nowa sesja, gdy już wczytała, czego potrzebuje;
    - K = koszt n pierwszych wywołań (USD po cenie modelu każdego wywołania albo — `jednostki` —
      dawne jednostki): jednorazowy koszt startu od nowa.
    Sesje krótsze niż n wywołań są pomijane; gdy nie zostaje żadna — ValueError."""
    if n < 1:
        raise ValueError(f"n = {n}: liczba wywołań startu musi być co najmniej 1")
    ok = [cs for cs in sesje if len(cs) >= n]
    if not ok:
        raise ValueError(f"brak głównych sesji z co najmniej {n} wywołaniami")
    rs = [context_size(cs[n - 1].counts) for cs in ok]
    ks = [_suma_kosztow(cs[:n], jednostki) for cs in ok]
    return {
        "n": n,
        "sesji": len(ok),
        "R": statistics.median(rs),
        "R_min": min(rs),
        "R_max": max(rs),
        "K": statistics.median(ks),
        "K_min": min(ks),
        "K_max": max(ks),
    }


def symuluj_prog(
    calls: list[Call],
    X: float,
    R: float,
    K: float,
    jednostki: bool = False,
    rozpoznaj_artefakty: bool = True,
) -> tuple[int, float]:
    """Jedna sesja „na niby”: gdy kontekst przekracza próg X, czyścimy ją (/clear + nota
    przekazania) — nowa sesja ma kontekst R i kosztuje jednorazowo K. Wynik: (liczba czyszczeń,
    oszczędność w USD — albo, `jednostki`, w jednostkach wejścia; ujemna = czyszczenia się nie
    zwróciły).

    `shift` = tokeny usunięte z początku kontekstu przez ostatnie czyszczenie; każde następne
    wywołanie czyta o tyle mniej. Ta część byłaby odczytem cache (cena odczytu modelu TEGO
    wywołania), a to, co z niej wykracza poza odczyt — zapisem cache po cenie zapisu tego wywołania
    (np. po przerwie > 1 h albo po przełączeniu modelu). Wywołanie modelu spoza cennika nie wnosi
    oszczędności (raport progów podaje liczbę takich wywołań).

    Wywołania idą po czasie, ale stan (`shift`, kontekst, model) każde bierze od swojego poprzednika
    w łańcuchu rozmowy (`Call.poprzednik`; nieznany = poprzednie wywołanie w czasie): drugi strumień
    zapytań w tym samym pliku i gałąź po cofnięciu rozmowy liczą się od miejsca, z którego wyszły.
    POCZATEK (wznowienie po streszczeniu) zeruje `shift`. Spadek kontekstu o więcej niż
    SPADEK_STRESZCZENIA względem poprzednika: przy tym samym modelu = streszczenie albo nowy początek
    (zeruje `shift`); przy zmianie modelu (Opus ↔ Fable) = z kontekstu wypadają bloki rozumowania
    drugiego modelu, to nie streszczenie — czyszczenie działa dalej, `shift` najwyżej do ctx − R.
    `rozpoznaj_artefakty=False` = dawna metoda (poprzednik = poprzednie wywołanie w czasie, każdy
    spadek zeruje `shift`) — do porównania, ile czyszczeń było artefaktami zapisu.

    Koszt K odejmujemy raz na końcu (czyszczenia × K): wynik jest dokładnie liniowy w K, a liczba
    czyszczeń od K nie zależy. Próg X ≤ R — ValueError (nowa sesja zaczynałaby już nad progiem)."""
    if X <= R:
        raise ValueError(
            f"próg X = {X / 1e3:g} tys. nie jest większy od kontekstu nowej sesji "
            f"R = {R / 1e3:g} tys."
        )
    # klucz wywołania → (shift, kontekst, model) po nim
    stany: dict[str, tuple[float, int, str]] = {}
    ostatni: tuple[float, int, str] | None = None
    clears, saved = 0, 0.0
    for call in calls:
        c = call.counts
        ctx = context_size(c)
        if not rozpoznaj_artefakty:
            prev = ostatni
        elif call.poprzednik == POCZATEK:
            prev = None
        else:
            prev = stany.get(call.poprzednik, ostatni)
        shift = prev[0] if prev else 0.0
        if prev is not None and ctx < prev[1] - SPADEK_STRESZCZENIA:
            if rozpoznaj_artefakty and call.model != prev[2]:
                shift = min(shift, max(0.0, ctx - R))  # przełączenie modelu, nie streszczenie
            else:
                shift = 0.0  # prawdziwe streszczenie: wcześniejsze czyszczenie przestaje działać
        if ctx - shift > X:
            shift = ctx - R
            clears += 1
        p = ceny_tokenu(call.model, jednostki)
        if shift > 0 and p is not None:
            cr, cw = c["cr"], c["cw5"] + c["cw1h"]
            w = p["cw1h"] if c["cw1h"] else p["cw5"]
            saved += p["cr"] * min(shift, cr) + w * max(0, min(shift - cr, cw))
        ostatni = (shift, ctx, call.model)
        if call.klucz:
            stany[call.klucz] = ostatni
    return clears, saved - clears * K


ARTEFAKTY = ("rozgalezienia", "poza_kolejnoscia", "przelaczenia_modelu", "poczatki_lancucha")


def artefakty_sesji(calls: list[Call]) -> dict[str, int]:
    """Zdarzenia w łańcuchu rozmowy jednej sesji (klucze ARTEFAKTY) — do raportu, czym dawna
    symulacja po czasie się myliła:
    - rozgalezienia: wywołanie dołącza do poprzednika, który ma już następcę (drugi strumień zapytań
      w tym samym pliku sesji, gałąź po cofnięciu rozmowy);
    - poza_kolejnoscia: poprzednik w łańcuchu ≠ poprzednie wywołanie w czasie (wywołania przeplecione
      z innym strumieniem — dawna metoda widziała tu fałszywe spadki kontekstu);
    - przelaczenia_modelu: spadek kontekstu o ponad SPADEK_STRESZCZENIA przy zmianie modelu względem
      poprzednika (bloki rozumowania drugiego modelu wypadają z kontekstu);
    - poczatki_lancucha: łańcuch zaczyna się od nowa w środku sesji (wznowienie po streszczeniu —
      prawdziwe streszczenie, nie artefakt)."""
    out = dict.fromkeys(ARTEFAKTY, 0)
    ctx_of: dict[str, tuple[int, str]] = {}
    z_nastepca: set[str] = set()
    poprz = None
    for i, call in enumerate(calls):
        ctx = context_size(call.counts)
        if call.poprzednik == POCZATEK:
            out["poczatki_lancucha"] += i > 0
            p = None
        elif call.poprzednik in ctx_of:
            p = call.poprzednik
            out["poza_kolejnoscia"] += p != poprz
        else:
            p = poprz
        if p is not None:
            out["rozgalezienia"] += p in z_nastepca
            z_nastepca.add(p)
            p_ctx, p_model = ctx_of[p]
            out["przelaczenia_modelu"] += (
                p_model != call.model and ctx < p_ctx - SPADEK_STRESZCZENIA
            )
        poprz = call.klucz or f"#{i}"
        ctx_of[poprz] = (ctx, call.model)
    return out


def _po_przekroczeniu(calls: list[Call], X: float) -> int | None:
    """Ile wywołań zostało w sesji PO pierwszym wywołaniu z kontekstem > X; None = nie przekroczyła."""
    for i, call in enumerate(calls):
        if context_size(call.counts) > X:
            return len(calls) - i - 1
    return None


def plaski_odcinek(wiersze: list[dict], tol: float = PLASKO_PKT) -> dict:
    """Płaski odcinek krzywej oszczędności (reguła T2, docs/rag/12): dla każdego mnożnika K progi X,
    których oszczędność (% kosztu) leży najwyżej `tol` pkt proc. poniżej najlepszego X; „wspolny” =
    progi płaskie przy K×1 i K×2 naraz. Tylko liczy — decyzję podpisuje człowiek w dokumentacji."""
    grupy: dict[float, list[dict]] = {}
    for w in wiersze:
        grupy.setdefault(w["mnoznik_K"], []).append(w)
    mn = []
    for m, ws in grupy.items():
        best = max(ws, key=lambda w: w["oszczednosc_pct"])
        mn.append(
            {
                "mnoznik_K": m,
                "najlepszy_prog": best["prog"],
                "najlepszy_pct": best["oszczednosc_pct"],
                "progi": [
                    w["prog"] for w in ws if w["oszczednosc_pct"] >= best["oszczednosc_pct"] - tol
                ],
            }
        )
    zb = [set(x["progi"]) for x in mn if x["mnoznik_K"] in (1, 2)]
    return {
        "tol_pkt": tol,
        "mnozniki": mn,
        "wspolny": sorted(zb[0] & zb[1]) if len(zb) == 2 else [],
    }


def _czas(ts: str) -> datetime | None:
    """Znacznik czasu zapisu (ISO, „Z” = UTC) → datetime z strefą; nieczytelny → None."""
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def raport_progow(
    scan: Scan,
    progi: tuple[int, ...] = PROGI_SYMULACJI,
    mnozniki: tuple[float, ...] = MNOZNIKI_K,
    teraz: datetime | None = None,
    jednostki: bool = False,
) -> dict:
    """Symulacja progów strażnika kontekstu na zakończonych sesjach głównych: parametry nowej sesji
    (R, K z zakresami), tabela próg × mnożnik K (czyszczenia, oszczędność, % kosztu tych sesji)
    z płaskim odcinkiem krzywej, ta sama tabela bez najdroższej sesji (R i K bez zmian), zwrot
    z jednego czyszczenia, artefakty zapisu i liczby per sesja dla PROG_SZCZEGOLOW (K×1).

    Koszt w USD po cenie modelu każdego wywołania (`jednostki` = dawne jednostki monitora). n* liczy
    się po cenie odczytu modelu większości wywołań. Sesje z wywołaniem w ostatnich SESJA_OTWARTA przed
    `teraz` (domyślnie: teraz) są pomijane i wypisane w „sesje_wykluczone” — mogą jeszcze trwać. Próg
    nie większy od R jest pomijany i trafia do „progi_pominiete”. Bez sesji do zmierzenia — ValueError.
    """
    teraz = teraz or datetime.now(timezone.utc)
    wszystkie = sesje_glowne(scan)
    otwarte = set()
    for i, cs in enumerate(wszystkie):
        t = _czas(cs[-1].ts)
        if t is not None and t >= teraz - SESJA_OTWARTA:
            otwarte.add(i)
    sesje = [cs for i, cs in enumerate(wszystkie) if i not in otwarte]
    if not sesje:
        raise ValueError(
            f"brak zakończonych głównych sesji z co najmniej {MIN_WYWOLAN_SESJI} wywołaniami"
        )
    par = parametry_nowej_sesji(sesje, jednostki=jednostki)
    R, K = par["R"], par["K"]
    koszty = [_suma_kosztow(cs, jednostki) for cs in sesje]
    top = max(range(len(sesje)), key=koszty.__getitem__)
    reszta = [i for i in range(len(sesje)) if i != top]
    dobre = [X for X in progi if X > R]

    def tabela(idx: list[int]) -> list[dict]:
        koszt = sum(koszty[i] for i in idx)
        wiersze = []
        for X in dobre:
            for m in mnozniki:
                wyniki = [symuluj_prog(sesje[i], X, R, K * m, jednostki) for i in idx]
                saved = sum(s for _, s in wyniki)
                wiersze.append(
                    {
                        "prog": X,
                        "mnoznik_K": m,
                        "czyszczen": sum(c for c, _ in wyniki),
                        "oszczednosc": saved,
                        "oszczednosc_pct": 100 * saved / koszt if koszt else 0.0,
                    }
                )
        return wiersze

    model_n = collections.Counter(c.model for cs in sesje for c in cs).most_common(1)[0][0]
    ceny_n = ceny_tokenu(model_n, jednostki)
    cena_odczytu = ceny_n["cr"] if ceny_n else None
    zwrot = []
    for X in dobre:
        po = [n for n in (_po_przekroczeniu(cs, X) for cs in sesje) if n is not None]
        zwrot.append(
            {
                "prog": X,
                "n_zwrotu": K / (cena_odczytu * (X - R)) if cena_odczytu else None,
                "sesji_ponad_progiem": len(po),
                "mediana_wywolan_po_przekroczeniu": statistics.median(po) if po else None,
            }
        )
    artefakty: dict = dict.fromkeys(ARTEFAKTY, 0)
    for cs in sesje:
        for k, v in artefakty_sesji(cs).items():
            artefakty[k] += v
    szczegoly = None
    if PROG_SZCZEGOLOW > R:
        szczegoly = {"prog": PROG_SZCZEGOLOW, "mnoznik_K": 1.0, "sesje": []}
        for cs, koszt in zip(sesje, koszty, strict=True):
            clears, saved = symuluj_prog(cs, PROG_SZCZEGOLOW, R, K, jednostki)
            szczegoly["sesje"].append(
                {
                    "sesja": cs[0].session,
                    "start": cs[0].ts,
                    "wywolan": len(cs),
                    "koszt": koszt,
                    "kontekst_max": max(context_size(c.counts) for c in cs),
                    "czyszczen": clears,
                    "czyszczen_bez_rozpoznania": symuluj_prog(
                        cs, PROG_SZCZEGOLOW, R, K, jednostki, rozpoznaj_artefakty=False
                    )[0],
                    "oszczednosc": saved,
                    "wywolan_po_przekroczeniu": _po_przekroczeniu(cs, PROG_SZCZEGOLOW),
                }
            )
        artefakty["prog"] = PROG_SZCZEGOLOW
        artefakty["czyszczen"] = sum(s["czyszczen"] for s in szczegoly["sesje"])
        artefakty["czyszczen_bez_rozpoznania"] = sum(
            s["czyszczen_bez_rozpoznania"] for s in szczegoly["sesje"]
        )
    naj = sesje[top]
    tab, tab_bez = tabela(list(range(len(sesje)))), tabela(reszta) if reszta else []
    return {
        "miara": "jednostki" if jednostki else "USD",
        "cennik": None if jednostki else CENNIK_DATA,
        "sesji": len(sesje),
        "min_wywolan": MIN_WYWOLAN_SESJI,
        "koszt_sesji": sum(koszty),
        "sesje_wykluczone": [
            {
                "sesja": cs[0].session,
                "start": cs[0].ts,
                "ostatnie": cs[-1].ts,
                "wywolan": len(cs),
            }
            for i, cs in enumerate(wszystkie)
            if i in otwarte
        ],
        "wywolan_bez_ceny": (
            0 if jednostki else sum(1 for cs in sesje for c in cs if c.usd is None)
        ),
        "parametry": par,
        "progi_pominiete": [X for X in progi if X <= R],
        "tabela": tab,
        "plaski_odcinek": plaski_odcinek(tab),
        "najdrozsza_sesja": {
            "sesja": naj[0].session,
            "start": naj[0].ts,
            "wywolan": len(naj),
            "koszt": koszty[top],
        },
        "tabela_bez_najdrozszej": tab_bez,
        "plaski_odcinek_bez_najdrozszej": plaski_odcinek(tab_bez),
        "koszt_bez_najdrozszej": sum(koszty[i] for i in reszta),
        "model_ceny_odczytu": model_n,
        "cena_odczytu": cena_odczytu,
        "zwrot": zwrot,
        "artefakty": artefakty,
        "sesje_przy_progu": szczegoly,
    }


def _pl(x: float) -> str:
    """Liczba w tekście po polsku: przecinek dziesiętny, bez zbędnych zer (0,1; 2)."""
    return f"{x:g}".replace(".", ",")


def _kwota(x: float, jednostki: bool, znak: bool = False, miara: bool = True) -> str:
    """Kwota w mierze symulacji: miliony dawnych jednostek wejścia (M) albo USD."""
    v = x / 1e6 if jednostki else x
    s = f"{v:+.2f}" if znak else f"{v:.2f}"
    return f"{s} {'M' if jednostki else 'USD'}" if miara else s


def _progi_tys(progi: list[float]) -> str:
    return ", ".join(f"{x / 1e3:.0f}" for x in progi) + " tys." if progi else "żaden"


def _tabela_progow(wiersze: list[dict], jednostki: bool = False) -> list[str]:
    """Wiersz na próg: liczba czyszczeń raz (nie zależy od K), potem oszczędność dla każdego K."""
    if not wiersze:
        return ["  brak progów do symulacji"]
    grupy: dict[float, list[dict]] = {}
    for w in wiersze:
        grupy.setdefault(w["prog"], []).append(w)
    etykiety = ["K×" + _pl(w["mnoznik_K"]) for w in next(iter(grupy.values()))]
    out = [f"  {'próg X':>10}  {'czyszczeń':>10}" + "".join(f"{e:>25}" for e in etykiety)]
    for prog, ws in grupy.items():
        cz = "/".join(str(c) for c in sorted({w["czyszczen"] for w in ws}))
        komorki = (
            f"{_kwota(w['oszczednosc'], jednostki, znak=True)} ({w['oszczednosc_pct']:+5.1f} %)"
            for w in ws
        )
        out.append(f"  {prog / 1e3:5.0f} tys.  {cz:>10}" + "".join(f"{k:>25}" for k in komorki))
    return out


def _plaski_tekst(p: dict) -> list[str]:
    """Płaski odcinek pod tabelą: progi do PLASKO_PKT pkt proc. od najlepszego, per K i łącznie."""
    if not p["mnozniki"]:
        return []
    czesci = [
        f"K×{_pl(m['mnoznik_K'])}: {_progi_tys(m['progi'])} (najlepszy {m['najlepszy_prog'] / 1e3:.0f})"
        for m in p["mnozniki"]
    ]
    return [
        f"  Do {_pl(p['tol_pkt'])} pkt proc. od najlepszego progu — " + "; ".join(czesci),
        f"  Płaski odcinek przy K×1 i K×2 naraz: {_progi_tys(p['wspolny'])}",
    ]


def raport_progow_tekst(r: dict) -> str:
    """Raport tekstowy symulacji progów (USD po cenie modelu albo miliony dawnych jednostek, M)."""
    p, naj, a = r["parametry"], r["najdrozsza_sesja"], r["artefakty"]
    jedn = r["miara"] == "jednostki"

    def kw(x: float, znak: bool = False, miara: bool = True) -> str:
        return _kwota(x, jedn, znak, miara)

    miara = (
        "Koszt w milionach dawnych jednostek wejścia (M) — ta sama waga dla każdego modelu."
        if jedn
        else f"Koszt w USD po cenie katalogowej modelu każdego wywołania (cennik z {r['cennik']})."
    )
    out = [
        "SYMULACJA PROGÓW STRAŻNIKA KONTEKSTU",
        "Co by było, gdyby główną sesję czyścić (/clear + nota przekazania) zawsze, gdy jej kontekst",
        "(tokeny czytane w jednym wywołaniu) przekroczy próg X.",
        miara,
        "",
        f"Dane: {r['sesji']} zakończonych głównych sesji z co najmniej {r['min_wywolan']} "
        f"wywołaniami, koszt rzeczywisty {kw(r['koszt_sesji'])}.",
    ]
    if r["sesje_wykluczone"]:
        out.append(
            f"Pominięte sesje z wywołaniem w ostatnich {SESJA_OTWARTA.seconds // 60} min "
            "(mogą jeszcze trwać):"
        )
        out += [
            f"  {s['sesja'][:8]} — ostatnie wywołanie {s['ostatnie'][:16].replace('T', ' ')} UTC, "
            f"{s['wywolan']} wywołań"
            for s in r["sesje_wykluczone"]
        ]
    if r["wywolan_bez_ceny"]:
        out.append(
            f"UWAGA: {r['wywolan_bez_ceny']} wywołań modeli spoza cennika liczy się jako 0 USD — "
            "koszty i oszczędności są zaniżone."
        )
    out += [
        "Nowa sesja po czyszczeniu (mediana z początków tych sesji, w nawiasie zakres):",
        f"  R = {p['R'] / 1e3:.0f} tys. tokenów ({p['R_min'] / 1e3:.0f}–{p['R_max'] / 1e3:.0f} "
        f"tys.) — kontekst po {p['n']}. wywołaniu: tyle czyta nowa sesja,",
        "      gdy już wczytała, czego potrzebuje;",
        f"  K = {kw(p['K'])} ({kw(p['K_min'], miara=False)}–{kw(p['K_max'])}) — koszt {p['n']} pierwszych "
        "wywołań: jednorazowy koszt startu od nowa.",
        "",
        "Oszczędność = tańsze wywołania po czyszczeniu (krótszy kontekst) minus K za każde czyszczenie.",
        "Wynik ujemny = czyszczenie się nie opłaca. K×0,5 i K×2 sprawdzają, czy wniosek przetrwa, gdy",
        "start nowej sesji kosztuje połowę albo dwa razy tyle. Symulacja idzie po łańcuchu rozmowy",
        f"(parentUuid). Spadek kontekstu o ponad {SPADEK_STRESZCZENIA / 1e3:.0f} tys. przy tym samym "
        "modelu (streszczenie rozmowy)",
        "kończy działanie wcześniejszego czyszczenia; spadek przy przełączeniu modelu — nie.",
    ]
    if r["progi_pominiete"]:
        out.append(
            "Pominięte progi (nie wyższe od R — nowa sesja zaczynałaby już nad nimi): "
            + ", ".join(f"{x / 1e3:.0f} tys." for x in r["progi_pominiete"])
        )
    out += ["", f"Wszystkie sesje ({r['sesji']}, koszt {kw(r['koszt_sesji'])}):"]
    out += _tabela_progow(r["tabela"], jedn) + _plaski_tekst(r["plaski_odcinek"])
    udzial = 100 * naj["koszt"] / (r["koszt_sesji"] or 1)
    out += [
        "",
        f"Bez najdroższej sesji {naj['sesja'][:8]} (start {naj['start'][:10]}, {naj['wywolan']} "
        f"wywołań, {kw(naj['koszt'])} = {udzial:.1f} % kosztu),",
        f"żeby jedna olbrzymia sesja nie przesądzała wniosku ({r['sesji'] - 1} sesji, koszt "
        f"{kw(r['koszt_bez_najdrozszej'])}; R i K bez zmian):",
    ]
    out += (
        _tabela_progow(r["tabela_bez_najdrozszej"], jedn)
        + _plaski_tekst(r["plaski_odcinek_bez_najdrozszej"])
        if r["tabela_bez_najdrozszej"]
        else ["  tylko jedna sesja — nie ma czego porównać"]
    )
    if jedn:
        cena, wzor = f"(waga {_pl(WEIGHTS['cr'])})", _pl(WEIGHTS["cr"])
    elif r["cena_odczytu"] is None:
        cena, wzor = f"(model {r['model_ceny_odczytu']} spoza cennika — n* nieznane)", "c"
    else:
        cena = (
            f"(c = {_pl(round(r['cena_odczytu'] * 1e6, 6))} USD za mln tokenów — cena odczytu "
            f"{r['model_ceny_odczytu']}, modelu większości wywołań)"
        )
        wzor = "c"
    out += [
        "",
        "Zwrot z jednego czyszczenia. Po czyszczeniu przy progu X każde następne wywołanie czyta",
        f"co najmniej X − R tokenów mniej z cache {cena}. Czyszczenie zwraca się więc po około",
        f"n* = K / ({wzor} · (X − R)) wywołaniach. Obok: ile wywołań naprawdę zostało w sesjach po",
        "pierwszym przekroczeniu progu (mediana). Więcej pozostałych wywołań niż n* = czyszczenie",
        "zwykle by się zwróciło.",
        f"  {'próg X':>10}  {'n*':>8}  {'sesji ponad progiem':>20}  "
        f"{'mediana wywołań po przekroczeniu':>33}",
    ]
    for z in r["zwrot"]:
        med = z["mediana_wywolan_po_przekroczeniu"]
        ponad = f"{z['sesji_ponad_progiem']} z {r['sesji']}"
        nz = "—" if z["n_zwrotu"] is None else f"{z['n_zwrotu']:.1f}"
        out.append(
            f"  {z['prog'] / 1e3:5.0f} tys.  {nz:>8}  {ponad:>20}  "
            f"{'—' if med is None else f'{med:g}':>33}"
        )
    out += [
        "",
        "Artefakty zapisu rozpoznane w łańcuchu rozmowy (dawna symulacja po czasie brała je za",
        "streszczenia i liczyła po nich nowe czyszczenia):",
        f"  rozgałęzienia łańcucha (drugi strumień zapytań w pliku sesji, gałąź po cofnięciu "
        f"rozmowy): {a['rozgalezienia']}; wywołania przeplecione z innym strumieniem: "
        f"{a['poza_kolejnoscia']}",
        f"  spadki kontekstu o ponad {SPADEK_STRESZCZENIA / 1e3:.0f} tys. przy przełączeniu modelu "
        f"(Opus ↔ Fable): {a['przelaczenia_modelu']}",
        f"  nowe łańcuchy w środku sesji (wznowienie po streszczeniu — prawdziwe streszczenia): "
        f"{a['poczatki_lancucha']}",
    ]
    if "czyszczen" in a:
        out.append(
            f"  czyszczenia przy progu {a['prog'] / 1e3:.0f} tys. (K×1): bez rozpoznania "
            f"{a['czyszczen_bez_rozpoznania']}, z rozpoznaniem {a['czyszczen']}"
        )
    if r["sesje_przy_progu"]:
        out += [
            "",
            f"Liczby per sesja dla progu {PROG_SZCZEGOLOW / 1e3:.0f} tys. (K×1): --progi --json, "
            "klucz „sesje_przy_progu”.",
        ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--katalog", type=Path, help="katalog zapisów (domyślnie: projekt z bieżącego katalogu)"
    )
    ap.add_argument("--od", default="", help="od dnia UTC, RRRR-MM-DD")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    tryb = ap.add_mutually_exclusive_group()
    tryb.add_argument(
        "--stan", type=Path, help="zapisz dokument strony „Tokeny CLAS-5” (i historię)"
    )
    tryb.add_argument(
        "--progi",
        action="store_true",
        help="symulacja progów strażnika kontekstu: co by było, gdyby czyścić sesję po "
        "przekroczeniu progu",
    )
    ap.add_argument(
        "--jednostki",
        action="store_true",
        help="z --progi: symulacja w dawnych jednostkach monitora zamiast USD",
    )
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.od and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.od):
        print("BŁĄD: --od w formacie RRRR-MM-DD", file=sys.stderr)
        return 2
    if a.jednostki and not a.progi:
        print("BŁĄD: --jednostki działa tylko z --progi", file=sys.stderr)
        return 2
    root = a.katalog or project_dir(Path.cwd())
    if not root.is_dir():
        print(f"BŁĄD: brak katalogu zapisów {root}", file=sys.stderr)
        return 1
    if a.stan:
        try:
            st = write_state(a.stan, scan_project(root, a.od))
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"BŁĄD: plik stanu {a.stan}: {e}", file=sys.stderr)
            return 1
        dni = st["dni"]
        print(
            f"stan strony: dni {len(dni)} ({dni[0]['d'] if dni else '-'} → "
            f"{dni[-1]['d'] if dni else '-'}), {a.stan.stat().st_size / 1e3:.0f} KB → {a.stan}"
        )
        return 0
    if a.progi:
        try:
            r = raport_progow(scan_project(root, a.od), jednostki=a.jednostki)
        except ValueError as e:
            print(f"BŁĄD: symulacja progów: {e}", file=sys.stderr)
            return 1
        print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else raport_progow_tekst(r))
        return 0
    s = summarize(scan_project(root, a.od))
    print(json.dumps(s, ensure_ascii=False, indent=1) if a.json else report(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
