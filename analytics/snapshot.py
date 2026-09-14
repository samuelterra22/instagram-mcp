#!/usr/bin/env python3
"""Snapshot diario de metricas -> acumula historico em CSV.

Rode 1x/dia (cron). Cada execucao grava:
- data/account_daily.csv : perfil + metricas de conta do dia
- data/posts.csv         : metricas dos posts recentes (para ranking/tendencia)
- data/demographics.csv  : demografia de seguidores (age/gender/city)

Idempotente por dia: se ja rodou hoje, substitui a linha do dia (nao duplica).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ig import IG, IGError, DATA_DIR, append_csv, read_csv, today_str  # noqa: E402


def dedupe_today(path: Path, day: str, key: str = "date") -> list[dict]:
    rows = [r for r in read_csv(path) if r.get(key) != day]
    return rows


def rewrite(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fieldnames})


def main() -> int:
    day = today_str(sys.argv[1] if len(sys.argv) > 1 else None)
    ig = IG()

    # ---- conta ----
    prof = ig.profile()
    try:
        totals = ig.account_totals("day")
    except IGError as e:
        print(f"aviso: account_totals falhou ({e}); seguindo so com perfil")
        totals = {}

    acc_fields = ["date", "followers_count", "follows_count", "media_count",
                  "reach", "profile_views", "accounts_engaged", "total_interactions",
                  "likes", "comments", "saves", "shares", "replies",
                  "follows_and_unfollows"]
    acc_row = {"date": day,
               "followers_count": prof.get("followers_count"),
               "follows_count": prof.get("follows_count"),
               "media_count": prof.get("media_count"),
               **{k: totals.get(k) for k in acc_fields if k in totals}}
    acc_path = DATA_DIR / "account_daily.csv"
    rows = dedupe_today(acc_path, day)
    rows.append(acc_row)
    rewrite(acc_path, rows, acc_fields)
    print(f"[account] {day}: {prof.get('followers_count')} seguidores, reach={totals.get('reach')}")

    # ---- posts ----
    posts = ig.recent_media(limit=25)
    post_fields = ["snapshot_date", "id", "timestamp", "media_type", "media_product_type",
                   "permalink", "reach", "likes", "comments", "saved", "shares",
                   "total_interactions", "profile_visits", "follows", "views",
                   "ig_reels_avg_watch_time", "caption_preview"]
    posts_path = DATA_DIR / "posts.csv"
    prows = dedupe_today(posts_path, day, key="snapshot_date")
    n_ok = 0
    for p in posts:
        is_reel = p.get("media_product_type") == "REELS"
        try:
            ins = ig.media_insights(p["id"], is_reel)
            n_ok += 1
        except IGError:
            ins = {}
        cap = (p.get("caption") or "").replace("\n", " ")[:80]
        prows.append({"snapshot_date": day, "id": p["id"], "timestamp": p.get("timestamp"),
                      "media_type": p.get("media_type"),
                      "media_product_type": p.get("media_product_type"),
                      "permalink": p.get("permalink"), "caption_preview": cap, **ins})
    rewrite(posts_path, prows, post_fields)
    print(f"[posts] {n_ok}/{len(posts)} posts com insights")

    # ---- demografia ----
    demo_fields = ["date", "breakdown", "dimension", "value"]
    demo_path = DATA_DIR / "demographics.csv"
    drows = dedupe_today(demo_path, day)
    for bd in ("age", "gender", "city"):
        try:
            res = ig.demographics(bd)
        except IGError:
            res = {}
        for dim, val in res.items():
            drows.append({"date": day, "breakdown": bd, "dimension": dim, "value": val})
    rewrite(demo_path, drows, demo_fields)
    print(f"[demografia] ok")

    print(f"snapshot {day} concluido em {DATA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
