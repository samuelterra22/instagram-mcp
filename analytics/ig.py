"""Cliente fino da Instagram Graph API para as rotinas de analytics.

Le credenciais do .env na raiz do projeto (mesmo arquivo do MCP server).
Nao imprime token. Usado por snapshot.py, report.py e benchmark.py.
"""
from __future__ import annotations

import os
import csv
import datetime as dt
from pathlib import Path
from typing import Any, Optional

import httpx

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def load_env() -> dict:
    """Le o .env da raiz do projeto para um dict, sem depender de shell."""
    env: dict[str, str] = {}
    envfile = ROOT / ".env"
    if not envfile.exists():
        raise SystemExit(f"ERRO: .env nao encontrado em {envfile}")
    for line in envfile.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


class IG:
    def __init__(self) -> None:
        env = load_env()
        self.token = env.get("INSTAGRAM_ACCESS_TOKEN")
        self.ig_id = env.get("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.api = env.get("INSTAGRAM_API_VERSION", "v19.0")
        self.base = env.get("INSTAGRAM_API_BASE_URL", "https://graph.facebook.com")
        if not self.token or not self.ig_id:
            raise SystemExit("ERRO: INSTAGRAM_ACCESS_TOKEN/BUSINESS_ACCOUNT_ID ausentes no .env")
        self._c = httpx.Client(timeout=30)

    def get(self, path: str, **params: Any) -> dict:
        params["access_token"] = self.token
        url = f"{self.base}/{self.api}/{path}"
        r = self._c.get(url, params=params)
        data = r.json()
        if isinstance(data, dict) and data.get("error"):
            raise IGError(data["error"].get("message", "erro desconhecido"),
                          data["error"].get("code"))
        return data

    # -- Perfil -----------------------------------------------------------
    def profile(self) -> dict:
        return self.get(
            self.ig_id,
            fields="username,name,followers_count,follows_count,media_count,biography,website",
        )

    # -- Insights de conta ------------------------------------------------
    def account_totals(self, period: str = "day") -> dict:
        """Metricas agregadas do periodo (total_value)."""
        metrics = ("reach,profile_views,accounts_engaged,total_interactions,"
                   "likes,comments,saves,shares,replies,follows_and_unfollows")
        d = self.get(f"{self.ig_id}/insights", metric=metrics, period=period,
                     metric_type="total_value")
        out = {}
        for m in d.get("data", []):
            tv = m.get("total_value") or {}
            out[m["name"]] = tv.get("value")
        return out

    def demographics(self, breakdown: str = "age") -> dict:
        """follower_demographics por breakdown: age|gender|city|country."""
        d = self.get(f"{self.ig_id}/insights", metric="follower_demographics",
                     period="lifetime", metric_type="total_value", breakdown=breakdown)
        for m in d.get("data", []):
            tv = m.get("total_value") or {}
            for br in tv.get("breakdowns", []):
                res = {}
                for item in br.get("results", []):
                    key = ",".join(item.get("dimension_values", []))
                    res[key] = item.get("value")
                return res
        return {}

    # -- Media ------------------------------------------------------------
    def recent_media(self, limit: int = 25) -> list[dict]:
        d = self.get(f"{self.ig_id}/media",
                     fields="id,caption,media_type,media_product_type,permalink,timestamp",
                     limit=limit)
        return d.get("data", [])

    def media_insights(self, media_id: str, is_reel: bool) -> dict:
        base = "reach,likes,comments,saved,shares,total_interactions"
        metrics = base + (",views,ig_reels_avg_watch_time" if is_reel
                          else ",profile_visits,follows")
        try:
            d = self.get(f"{media_id}/insights", metric=metrics)
        except IGError:
            # fallback: alguns posts antigos nao suportam certas metricas
            d = self.get(f"{media_id}/insights", metric=base)
        return {m["name"]: (m.get("values", [{}])[0].get("value")
                            if m.get("values") else
                            (m.get("total_value") or {}).get("value"))
                for m in d.get("data", [])}

    # -- Concorrentes -----------------------------------------------------
    def business_discovery(self, username: str) -> dict:
        username = username.lstrip("@").strip()
        fields = ("business_discovery.username(" + username +
                  "){id,username,name,followers_count,follows_count,media_count,biography,website}")
        d = self.get(self.ig_id, fields=fields)
        return d.get("business_discovery", {})


class IGError(Exception):
    def __init__(self, message: str, code: Optional[int] = None) -> None:
        super().__init__(message)
        self.code = code


# -- utilidades de CSV ---------------------------------------------------
def append_csv(path: Path, row: dict, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k) for k in fieldnames})


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def today_str(env_date: Optional[str] = None) -> str:
    """Data de hoje. Aceita override via arg (evita divergencia em teste)."""
    if env_date:
        return env_date
    return dt.datetime.now(dt.timezone.utc).date().isoformat()
