#!/usr/bin/env python3
"""Benchmarking de concorrentes (rotina R5 do playbook).

Le a lista de @ em analytics/competitors.txt (um por linha, # = comentario) ou
recebe @ como argumentos. Usa business_discovery em cada um, acumula em
data/competitors.csv e imprime comparativo (inclui a propria conta) + variacao
vs a ultima medicao.

Uso:
  python analytics/benchmark.py                 # le competitors.txt
  python analytics/benchmark.py natgeo nasa     # ad-hoc
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ig import IG, IGError, DATA_DIR, append_csv, read_csv, today_str  # noqa: E402

FIELDS = ["date", "username", "name", "followers_count", "follows_count", "media_count"]


def load_list() -> list[str]:
    f = Path(__file__).resolve().parent / "competitors.txt"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line.lstrip("@"))
    return out


def prev_value(rows: list[dict], username: str, today: str) -> dict | None:
    hist = [r for r in rows if r["username"] == username and r["date"] != today]
    return sorted(hist, key=lambda r: r["date"])[-1] if hist else None


def main() -> int:
    day = today_str()
    handles = [a.lstrip("@") for a in sys.argv[1:]] or load_list()
    ig = IG()

    # inclui a propria conta como referencia
    me = ig.profile()
    path = DATA_DIR / "competitors.csv"
    existing = read_csv(path)

    rows_out = []
    # propria conta
    rows_out.append({"date": day, "username": me.get("username"), "name": me.get("name"),
                     "followers_count": me.get("followers_count"),
                     "follows_count": me.get("follows_count"),
                     "media_count": me.get("media_count"), "_me": True})

    for h in handles:
        try:
            bd = ig.business_discovery(h)
            rows_out.append({"date": day, "username": bd.get("username"), "name": bd.get("name"),
                             "followers_count": bd.get("followers_count"),
                             "follows_count": bd.get("follows_count"),
                             "media_count": bd.get("media_count")})
        except IGError as e:
            print(f"aviso: {h} falhou ({e})")

    for r in rows_out:
        append_csv(path, r, FIELDS)

    # ---- comparativo ----
    rows_out.sort(key=lambda r: int(r.get("followers_count") or 0), reverse=True)
    print(f"\n=== Benchmark {day} (ordenado por seguidores) ===")
    print(f"{'conta':<28}{'seguidores':>12}{'posts':>8}{'delta seg.':>12}")
    for r in rows_out:
        u = ("* " if r.get("_me") else "  ") + (r.get("username") or "?")
        prev = prev_value(existing, r.get("username"), day)
        delta = ""
        if prev:
            d = int(r.get("followers_count") or 0) - int(prev.get("followers_count") or 0)
            delta = f"{'+' if d >= 0 else ''}{d}"
        print(f"{u:<28}{str(r.get('followers_count') or '-'):>12}"
              f"{str(r.get('media_count') or '-'):>8}{delta:>12}")
    print("\n* = sua conta. delta = variacao vs ultima medicao registrada.")
    if not handles:
        print("\n(sem concorrentes: preencha analytics/competitors.txt ou passe @ como argumento)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
