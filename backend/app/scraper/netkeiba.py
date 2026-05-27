"""
netkeiba.com scraper — prototype use only.

IMPORTANT:
- robots.txt を必ず確認してください: https://db.netkeiba.com/robots.txt
- リクエスト間隔: 最低 2 秒（SCRAPER_DELAY 環境変数で変更可）
- 商用利用前に JRA-VAN データサービスへ移行すること
- User-Agent を正直に設定済み
"""
import httpx
import asyncio
import logging
import re
from bs4 import BeautifulSoup
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
DELAY    = float(os.getenv("SCRAPER_DELAY", "2"))
BASE_URL = "https://db.netkeiba.com"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (compatible; BarokuResearchBot/0.1; prototype)",
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}


# ── Fetch ──────────────────────────────────────────────────────────────

async def fetch_horse(client: httpx.AsyncClient, horse_id: str) -> Optional[dict]:
    url = f"{BASE_URL}/horse/{horse_id}/"
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        # netkeiba は EUC-JP
        html = resp.content.decode("EUC-JP", errors="replace")
        return parse_horse_page(html, horse_id)
    except Exception as e:
        logger.error(f"[{horse_id}] fetch failed: {e}")
        return None


async def scrape_horses(horse_ids: list[str]) -> list[dict]:
    """Rate-limited batch scrape. Checks robots.txt first."""
    results = []
    async with httpx.AsyncClient() as client:
        try:
            robots = await client.get(
                f"{BASE_URL}/robots.txt", headers=HEADERS, timeout=5.0
            )
            logger.info(f"robots.txt: HTTP {robots.status_code}")
            if "Disallow: /horse/" in robots.text:
                logger.warning("robots.txt disallows /horse/ — aborting scrape")
                return []
        except Exception as e:
            logger.warning(f"robots.txt check failed: {e}")

        for horse_id in horse_ids:
            logger.info(f"Scraping {horse_id} ...")
            result = await fetch_horse(client, horse_id)
            if result:
                results.append(result)
                logger.info(f"  ✓ {result.get('name', '?')}")
            else:
                logger.warning(f"  ✗ skipped {horse_id}")
            await asyncio.sleep(DELAY)

    return results


# ── Parse ──────────────────────────────────────────────────────────────

def parse_horse_page(html: str, horse_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"netkeiba_id": horse_id}

    # ── 馬名 ──
    title_div = soup.find("div", class_="horse_title")
    if title_div:
        h1 = title_div.find("h1")
        if h1:
            data["name"] = h1.get_text(strip=True)
        # English name often in <p class="eng">
        eng = title_div.find("p", class_="eng")
        if eng:
            data["name_en"] = eng.get_text(strip=True)

    # ── プロフィールテーブル ──
    prof = soup.find("table", class_="db_prof_table")
    if prof:
        for row in prof.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            val = td.get_text(strip=True)

            if key == "生年月日":
                m = re.match(r"(\d{4})", val)
                data["born_year"] = int(m.group(1)) if m else None
            elif key == "性齢":
                # e.g. "牡5" or "牝3"
                if val:
                    data["sex"] = val[0] if val[0] in ("牡", "牝", "騸") else None
            elif key == "毛色":
                data["color"] = val
            elif key == "調教師":
                data["trainer"] = re.sub(r"\s+", " ", val).strip()
            elif key == "馬主":
                data["owner"] = val
            elif key == "生産者":
                data["farm"] = val
            elif key == "産地":
                data["birthplace"] = val
            elif key == "セリ名称":
                pass  # skip
            elif key == "獲得賞金":
                # e.g. "11億7366万7000円"
                nums = re.sub(r"[^\d]", "", val)
                data["earnings"] = int(nums) if nums else 0

    # ── 性別・ステータス ──
    if "sex" not in data or not data.get("sex"):
        # fallback from title area
        title_text = (title_div.get_text() if title_div else "")
        for s in ("牡", "牝", "騸"):
            if s in title_text:
                data["sex"] = s
                break

    # ── 血統（3代）──
    blood = soup.find("table", class_="blood_table")
    if not blood:
        blood = soup.find("table", summary="5代血統表")
    if blood:
        cells = [td.get_text(strip=True) for td in blood.find_all("td")]
        # netkeiba 5代血統表の先頭セルは:
        # [0]=父, [1]=父父, [2]=父父父, [3]=父父母, [4]=父母, [5]=父母父, [6]=父母母
        # [7]=母, [8]=母父, [9]=母父父, [10]=母父母, [11]=母母, [12]=母母父, [13]=母母母
        # ※レイアウトはページバージョンにより異なる場合あり
        if len(cells) >= 14:
            data.setdefault("sire",         cells[0])
            data.setdefault("sire_of_sire", cells[1])
            data.setdefault("dam_of_sire",  cells[4])
            data.setdefault("dam",          cells[7])
            data.setdefault("sire_of_dam",  cells[8])
            data.setdefault("dam_of_dam",   cells[11])
        elif len(cells) >= 4:
            data.setdefault("sire", cells[0])
            data.setdefault("dam",  cells[len(cells) // 2])

    # ── レース成績サマリ ──
    result_div = soup.find("div", class_="db_h_race_results")
    if not result_div:
        result_div = soup.find("div", id="contents")

    # G1勝利数・通算成績
    g1_wins = 0
    wins = places = losses = 0
    races_data = []

    race_table = None
    if result_div:
        race_table = result_div.find("table")
    if not race_table:
        # テーブルを直接探す
        for tbl in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
            if "着順" in headers or "レース名" in headers:
                race_table = tbl
                break

    if race_table:
        th_texts = [th.get_text(strip=True) for th in race_table.find_all("th")]
        col_map = {v: i for i, v in enumerate(th_texts)}
        for tr in race_table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue
            try:
                def cell(key, fallback=""):
                    idx = col_map.get(key)
                    return tds[idx].get_text(strip=True) if idx is not None and idx < len(tds) else fallback

                pos_str = cell("着順", "")
                pos = None
                if pos_str.isdigit():
                    pos = int(pos_str)
                elif pos_str in ("取消", "除外", "中止"):
                    continue

                grade = cell("グレード") or cell("格") or ""
                race_name = cell("レース名", "")
                date = cell("日付") or cell("開催日", "")
                jockey = cell("騎手", "")
                time_str = cell("タイム", "")
                dist = cell("距離", "")
                course = cell("開催", "") or cell("コース", "")
                prize_str = re.sub(r"[^\d]", "", cell("賞金", "") or "")
                prize = int(prize_str) * 10000 if prize_str else 0  # 万円→円

                if pos == 1:
                    wins += 1
                    if "G1" in grade or "G1" in race_name:
                        g1_wins += 1
                elif pos in (2, 3):
                    places += 1
                else:
                    losses += 1

                races_data.append({
                    "date": date,
                    "race_name": race_name,
                    "grade": grade,
                    "position": pos,
                    "jockey": jockey,
                    "time": time_str,
                    "distance": dist,
                    "course": course,
                    "prize": prize,
                })
            except Exception:
                continue

    data["g1_wins"]  = g1_wins
    data["wins"]     = wins
    data["places"]   = places
    data["losses"]   = losses
    data["win_rate"] = round(wins / max(wins + losses, 1) * 100)
    data["races"]    = races_data

    return data
