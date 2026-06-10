"""
netkeiba.com の race.netkeiba.com から JRA レースの出馬表・結果を取得する — プロトタイプ用。

IMPORTANT:
- robots.txt を必ず確認してください: https://race.netkeiba.com/robots.txt
- リクエスト間隔: 最低 2 秒（SCRAPER_DELAY 環境変数で変更可）
- 商用利用前に JRA-VAN データサービスへ移行すること
- サイト構造の変更により解析が失敗する可能性があるため、
  各関数は失敗時に None / 空リストを返し、呼び出し側で握りつぶせるようにしている。
"""
from __future__ import annotations

import re
import asyncio
import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
DELAY = float(os.getenv("SCRAPER_DELAY", "2"))
RACE_BASE = "https://race.netkeiba.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BarokuResearchBot/0.1; prototype)",
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

# netkeiba race_id の競馬場コード（5-6桁目）。JRA中央競馬のみ対応。
VENUE_CODES = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟", "05": "東京",
    "06": "中山", "07": "中京", "08": "京都", "09": "阪神", "10": "小倉",
}


# ── 日付ユーティリティ ─────────────────────────────────────────────────

def upcoming_weekend_dates(today: Optional[date] = None) -> list[str]:
    """直近の土日（今日が土日ならその週末）を YYYYMMDD のリストで返す。"""
    today = today or date.today()
    if today.weekday() == 5:  # Sat
        saturday = today
    elif today.weekday() == 6:  # Sun
        saturday = today - timedelta(days=1)
    else:
        saturday = today + timedelta(days=(5 - today.weekday()) % 7)
    sunday = saturday + timedelta(days=1)
    return [saturday.strftime("%Y%m%d"), sunday.strftime("%Y%m%d")]


def previous_weekend_dates(today: Optional[date] = None) -> list[str]:
    """1つ前の週末（先週の土日）を YYYYMMDD のリストで返す。"""
    sat_str, _ = upcoming_weekend_dates(today)
    saturday = date(int(sat_str[:4]), int(sat_str[4:6]), int(sat_str[6:]))
    last_saturday = saturday - timedelta(days=7)
    last_sunday = last_saturday + timedelta(days=1)
    return [last_saturday.strftime("%Y%m%d"), last_sunday.strftime("%Y%m%d")]


def historical_weekend_dates(weeks: int, today: Optional[date] = None) -> list[str]:
    """直近 `weeks` 週分の過去の土日を YYYYMMDD のリストで返す（バックフィル用）。"""
    sat_str, _ = previous_weekend_dates(today)
    saturday = date(int(sat_str[:4]), int(sat_str[4:6]), int(sat_str[6:]))

    dates: list[str] = []
    for i in range(weeks):
        sat = saturday - timedelta(days=7 * i)
        sun = sat + timedelta(days=1)
        dates.append(sat.strftime("%Y%m%d"))
        dates.append(sun.strftime("%Y%m%d"))
    return dates


# ── HTML 解析ヘルパー ──────────────────────────────────────────────────

def _to_int(s: str) -> Optional[int]:
    s = re.sub(r"[^\d-]", "", s or "")
    return int(s) if s and s not in ("-",) else None


def _to_float(s: str) -> Optional[float]:
    s = re.sub(r"[^\d.-]", "", s or "")
    try:
        return float(s) if s and s not in ("-", ".", "-.") else None
    except ValueError:
        return None


def _find_table_by_headers(soup: BeautifulSoup, required_headers: list[str]):
    for tbl in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        if all(h in headers for h in required_headers):
            return tbl, headers
    return None, None


# ── robots.txt チェック ───────────────────────────────────────────────

async def check_robots(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get(f"{RACE_BASE}/robots.txt", headers=HEADERS, timeout=5.0)
        if "Disallow: /race/" in resp.text or "Disallow: /top/race_list" in resp.text:
            logger.warning("robots.txt disallows race scraping — aborting")
            return False
    except Exception as e:
        logger.warning(f"robots.txt check failed: {e}")
    return True


# ── 開催日のレース一覧 ──────────────────────────────────────────────────

async def fetch_race_list(client: httpx.AsyncClient, kaisai_date: str) -> list[dict]:
    """指定日(YYYYMMDD)に開催されるJRAレースの基本情報を取得する。"""
    url = f"{RACE_BASE}/top/race_list.html?kaisai_date={kaisai_date}"
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        html = resp.content.decode("EUC-JP", errors="replace")
    except Exception as e:
        logger.error(f"race_list fetch failed ({kaisai_date}): {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    races: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        m = re.search(r"race_id=(\d{12})", a["href"])
        if not m:
            continue
        race_id = m.group(1)
        if race_id in seen:
            continue
        seen.add(race_id)

        venue_code = race_id[4:6]
        racecourse = VENUE_CODES.get(venue_code)
        if not racecourse:
            continue  # JRA以外（地方競馬場コード）は対象外

        text = a.get_text(strip=True)
        race_number_m = re.search(r"(\d{1,2})\s*R", text)

        races.append({
            "race_id": race_id,
            "racecourse": racecourse,
            "date": f"{kaisai_date[:4]}-{kaisai_date[4:6]}-{kaisai_date[6:]}",
            "race_number": int(race_number_m.group(1)) if race_number_m else None,
            "race_name_hint": text,
        })

    return races


# ── 出馬表（出走予定馬の情報・調教情報）─────────────────────────────────

async def fetch_shutuba(client: httpx.AsyncClient, race_id: str) -> Optional[dict]:
    url = f"{RACE_BASE}/race/shutuba.html?race_id={race_id}"
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        html = resp.content.decode("EUC-JP", errors="replace")
        return parse_shutuba(html, race_id)
    except Exception as e:
        logger.error(f"shutuba fetch failed ({race_id}): {e}")
        return None


def _parse_race_header(soup: BeautifulSoup) -> dict:
    """ページ上部のテキストからレース概要（距離・馬場・グレード等）を正規表現で抽出する。"""
    data: dict = {}
    header_text = soup.get_text(" ", strip=True)[:1000]

    m = re.search(r"(芝|ダ|障)\s*(右|左|直線)?\s*(\d{3,4})m", header_text)
    if m:
        surface_char = m.group(1)
        data["surface"] = {"芝": "芝", "ダ": "ダート", "障": "障害"}.get(surface_char, surface_char)
        data["direction"] = m.group(2)
        data["distance"] = int(m.group(3))

    grade_m = re.search(r"\(?(G[123]|J[GR]?[123]|OP|L)\)?", header_text)
    data["grade"] = grade_m.group(1) if grade_m else None

    weather_m = re.search(r"天候\s*[:：]?\s*(晴|曇|雨|小雨|雪|小雪)", header_text)
    data["weather"] = weather_m.group(1) if weather_m else None

    cond_m = re.search(r"馬場\s*[:：]?\s*(良|稍重|重|不良)", header_text)
    data["track_condition"] = cond_m.group(1) if cond_m else None

    h1 = soup.find("h1")
    data["race_name"] = h1.get_text(strip=True) if h1 else None

    return data


def parse_shutuba(html: str, race_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"race_id": race_id, "entries": []}
    data.update(_parse_race_header(soup))

    # 出走馬一覧テーブル
    table, headers = _find_table_by_headers(soup, ["馬番", "馬名"])
    if not table:
        return data

    col_map = {h: i for i, h in enumerate(headers)}

    def cell(tds, key, fallback=""):
        idx = col_map.get(key)
        return tds[idx].get_text(strip=True) if idx is not None and idx < len(tds) else fallback

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        horse_link = tr.find("a", href=re.compile(r"/horse/\w+"))
        netkeiba_horse_id = None
        if horse_link:
            hm = re.search(r"/horse/(\w+)", horse_link["href"])
            netkeiba_horse_id = hm.group(1) if hm else None

        weight_str = cell(tds, "斤量")
        horse_weight_str = cell(tds, "馬体重")
        wm = re.match(r"(\d+)\(([+-]?\d+)\)", horse_weight_str)

        data["entries"].append({
            "netkeiba_horse_id": netkeiba_horse_id,
            "horse_name": horse_link.get_text(strip=True) if horse_link else cell(tds, "馬名"),
            "post_position": _to_int(cell(tds, "枠")),
            "horse_number": _to_int(cell(tds, "馬番")),
            "jockey": cell(tds, "騎手"),
            "weight_carried": _to_float(weight_str),
            "horse_weight": int(wm.group(1)) if wm else None,
            "horse_weight_diff": int(wm.group(2)) if wm else None,
            "odds_win": _to_float(cell(tds, "オッズ") or cell(tds, "単勝")),
            "popularity": _to_int(cell(tds, "人気")),
        })

    return data


# ── レース結果（着順）──────────────────────────────────────────────────

async def fetch_results(client: httpx.AsyncClient, race_id: str) -> Optional[dict]:
    url = f"{RACE_BASE}/race/result.html?race_id={race_id}"
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        html = resp.content.decode("EUC-JP", errors="replace")
        return parse_results(html, race_id)
    except Exception as e:
        logger.error(f"results fetch failed ({race_id}): {e}")
        return None


def parse_results(html: str, race_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"race_id": race_id, "results": {}, "finished": False}

    table, headers = _find_table_by_headers(soup, ["着順", "馬番"])
    if not table:
        return data

    col_map = {h: i for i, h in enumerate(headers)}
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        pos_str = tds[col_map["着順"]].get_text(strip=True)
        num_str = tds[col_map["馬番"]].get_text(strip=True)
        if not pos_str.isdigit() or not num_str.isdigit():
            continue
        data["results"][int(num_str)] = int(pos_str)

    data["finished"] = len(data["results"]) > 0
    return data


# ── 過去レースの結果ページ（出走馬情報＋着順をまとめて取得）──────────────

async def fetch_result_entries(client: httpx.AsyncClient, race_id: str) -> Optional[dict]:
    """確定済みレースの結果ページから、出走馬情報と着順をまとめて取得する（バックフィル用）。"""
    url = f"{RACE_BASE}/race/result.html?race_id={race_id}"
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        html = resp.content.decode("EUC-JP", errors="replace")
        return parse_result_full(html, race_id)
    except Exception as e:
        logger.error(f"result entries fetch failed ({race_id}): {e}")
        return None


def parse_result_full(html: str, race_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"race_id": race_id, "entries": [], "finished": False}
    data.update(_parse_race_header(soup))

    table, headers = _find_table_by_headers(soup, ["着順", "馬番", "馬名"])
    if not table:
        return data

    col_map = {h: i for i, h in enumerate(headers)}

    def cell(tds, key, fallback=""):
        idx = col_map.get(key)
        return tds[idx].get_text(strip=True) if idx is not None and idx < len(tds) else fallback

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        pos_str = cell(tds, "着順")
        if not pos_str.isdigit():
            continue

        horse_link = tr.find("a", href=re.compile(r"/horse/\w+"))
        netkeiba_horse_id = None
        if horse_link:
            hm = re.search(r"/horse/(\w+)", horse_link["href"])
            netkeiba_horse_id = hm.group(1) if hm else None

        weight_str = cell(tds, "斤量")
        horse_weight_str = cell(tds, "馬体重")
        wm = re.match(r"(\d+)\(([+-]?\d+)\)", horse_weight_str)

        data["entries"].append({
            "netkeiba_horse_id": netkeiba_horse_id,
            "horse_name": horse_link.get_text(strip=True) if horse_link else cell(tds, "馬名"),
            "post_position": _to_int(cell(tds, "枠")),
            "horse_number": _to_int(cell(tds, "馬番")),
            "jockey": cell(tds, "騎手"),
            "weight_carried": _to_float(weight_str),
            "horse_weight": int(wm.group(1)) if wm else None,
            "horse_weight_diff": int(wm.group(2)) if wm else None,
            "odds_win": _to_float(cell(tds, "単勝")),
            "popularity": _to_int(cell(tds, "人気")),
            "result_position": int(pos_str),
        })

    data["finished"] = len(data["entries"]) > 0
    return data


# ── レート制限つきバッチ取得 ──────────────────────────────────────────

async def sleep_between_requests() -> None:
    await asyncio.sleep(DELAY)
