#!/usr/bin/env python3
"""Relatorio de performance do perfil (rotinas R1+R2 do playbook).

Le o historico acumulado (data/*.csv) e dados ao vivo, e gera um relatorio
markdown em reports/ com: crescimento, ranking de posts por CONVERSAO (follows)
e por alcance, feed vs reels, demografia e recomendacoes acionaveis.

Uso: python analytics/report.py [YYYY-MM-DD]
Degrada com pouco historico (avisa quando nao da pra comparar semana a semana).
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ig import DATA_DIR, REPORTS_DIR, read_csv, today_str  # noqa: E402


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def fmt(v):
    n = num(v, None)
    if n is None:
        return "-"
    return str(int(n)) if n == int(n) else f"{n:.1f}"


def latest_posts(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    last = max(r["snapshot_date"] for r in rows)
    return [r for r in rows if r["snapshot_date"] == last]


def eng_rate(p: dict) -> float:
    r = num(p.get("reach"))
    return (num(p.get("total_interactions")) / r * 100) if r else 0.0


def section_growth(acc: list[dict]) -> list[str]:
    out = ["## Crescimento"]
    if not acc:
        return out + ["Sem dados de conta ainda. Rode o snapshot diariamente."]
    acc = sorted(acc, key=lambda r: r["date"])
    cur = acc[-1]
    out.append(f"- Seguidores hoje ({cur['date']}): **{fmt(cur.get('followers_count'))}** "
               f"| seguindo {fmt(cur.get('follows_count'))} | posts {fmt(cur.get('media_count'))}")
    if len(acc) >= 2:
        prev = acc[-2]
        delta = num(cur.get("followers_count")) - num(prev.get("followers_count"))
        out.append(f"- Variacao vs {prev['date']}: **{'+' if delta >= 0 else ''}{fmt(delta)}** seguidores")
    # janela 7d
    if len(acc) >= 8:
        wk = acc[-7:]
        rch = sum(num(r.get("reach")) for r in wk)
        inter = sum(num(r.get("total_interactions")) for r in wk)
        out.append(f"- Ultimos 7 dias: alcance somado **{fmt(rch)}**, interacoes **{fmt(inter)}**")
    else:
        out.append(f"- (historico curto: {len(acc)} dia(s). Semana a semana aparece com ~8 dias de snapshot.)")
    return out


def section_posts(posts: list[dict]) -> list[str]:
    out = ["## Posts recentes - conversao e alcance"]
    if not posts:
        return out + ["Sem posts com insights."]
    for p in posts:
        p["_eng"] = eng_rate(p)
    by_follows = sorted(posts, key=lambda p: num(p.get("follows")), reverse=True)
    by_reach = sorted(posts, key=lambda p: num(p.get("reach")), reverse=True)
    by_eng = sorted(posts, key=lambda p: p["_eng"], reverse=True)

    def line(p):
        cap = (p.get("caption_preview") or "").strip()[:60]
        return (f"  - [{p.get('media_product_type') or p.get('media_type')}] "
                f"reach {fmt(p.get('reach'))} | inter {fmt(p.get('total_interactions'))} "
                f"({p['_eng']:.1f}%) | saves {fmt(p.get('saved'))} | shares {fmt(p.get('shares'))} "
                f"| visitas {fmt(p.get('profile_visits'))} | segue {fmt(p.get('follows'))}\n"
                f"    {cap} -> {p.get('permalink')}")

    out.append("### Top 3 por CONVERSAO (novos seguidores)")
    out += [line(p) for p in by_follows[:3]]
    out.append("### Top 3 por ALCANCE")
    out += [line(p) for p in by_reach[:3]]
    out.append("### Top 3 por TAXA DE ENGAJAMENTO")
    out += [line(p) for p in by_eng[:3]]
    return out


def section_format(posts: list[dict]) -> list[str]:
    out = ["## Feed vs Reels"]
    groups = {"REELS": [], "FEED": []}
    for p in posts:
        key = "REELS" if p.get("media_product_type") == "REELS" else "FEED"
        groups[key].append(p)
    for key, ps in groups.items():
        if not ps:
            continue
        n = len(ps)
        avg = lambda f: sum(num(p.get(f)) for p in ps) / n
        out.append(f"- **{key}** ({n}): reach medio {avg('reach'):.0f} | "
                   f"interacoes medias {avg('total_interactions'):.0f} | "
                   f"saves {avg('saved'):.1f} | shares {avg('shares'):.1f} | "
                   f"novos seguidores medios {avg('follows'):.1f}")
    return out


def section_demographics(demo: list[dict], day: str) -> list[str]:
    out = ["## Audiencia (seguidores)"]
    today = [d for d in demo if d["date"] == day] or demo
    for bd in ("age", "gender", "city"):
        items = [(d["dimension"], num(d["value"])) for d in today if d["breakdown"] == bd]
        items.sort(key=lambda x: x[1], reverse=True)
        if not items:
            continue
        top = ", ".join(f"{k} ({int(v)})" for k, v in items[:4])
        out.append(f"- **{bd}**: {top}")
    return out


def section_reco(posts: list[dict], demo: list[dict], day: str) -> list[str]:
    out = ["## Recomendacoes (acionaveis)"]
    if not posts:
        return out + ["- Sem dados suficientes."]
    reels = [p for p in posts if p.get("media_product_type") == "REELS"]
    feed = [p for p in posts if p.get("media_product_type") != "REELS"]
    def avg(ps, f):
        return sum(num(p.get(f)) for p in ps) / len(ps) if ps else 0
    # 1. formato que converte mais
    if reels and feed:
        if avg(reels, "follows") > avg(feed, "follows"):
            out.append("- Reels trazem mais SEGUIDORES que feed. Aumente a frequencia de reels.")
        else:
            out.append("- Feed converte tanto quanto ou mais que reels aqui. Nao abandone o feed.")
        if avg(reels, "reach") > avg(feed, "reach") * 1.3:
            out.append("- Reels alcancam bem mais gente (descoberta). Use reel para topo de funil.")
    # 2. post campeao de conversao
    champ = max(posts, key=lambda p: num(p.get("follows")))
    if num(champ.get("follows")) > 0:
        out.append(f"- Post que MAIS trouxe seguidores: {champ.get('permalink')} "
                   f"({fmt(champ.get('follows'))}). Replique o tema/gancho.")
    else:
        out.append("- Nenhum post recente converteu em seguidor. Reforce CTA de 'seguir' e "
                   "otimize a bio/destaques (o conteudo alcanca, mas nao converte).")
    # 3. saves/shares
    best_save = max(posts, key=lambda p: num(p.get("saved")))
    if num(best_save.get("saved")) > 0:
        out.append(f"- Conteudo mais SALVO: {best_save.get('permalink')} "
                   f"({fmt(best_save.get('saved'))} saves). Save = alto valor percebido; faca serie disso.")
    # 4. demografia -> conteudo
    ages = [(d["dimension"], num(d["value"])) for d in demo if d["breakdown"] == "age" and d["date"] == day]
    if ages:
        top_age = max(ages, key=lambda x: x[1])[0]
        out.append(f"- Maior faixa de seguidores: {top_age}. Ajuste linguagem, horario e temas a esse publico.")
    return out


def main() -> int:
    day = today_str(sys.argv[1] if len(sys.argv) > 1 else None)
    acc = read_csv(DATA_DIR / "account_daily.csv")
    posts = latest_posts(read_csv(DATA_DIR / "posts.csv"))
    demo = read_csv(DATA_DIR / "demographics.csv")

    lines = [f"# Relatorio Instagram - @positivamenteclinicaesp",
             f"Gerado para {day}", ""]
    lines += section_growth(acc) + [""]
    lines += section_posts(posts) + [""]
    lines += section_format(posts) + [""]
    lines += section_demographics(demo, day) + [""]
    lines += section_reco(posts, demo, day) + [""]
    report = "\n".join(lines)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report-{day}.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[salvo em {out_path}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
