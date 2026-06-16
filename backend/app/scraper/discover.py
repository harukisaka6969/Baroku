"""
netkeibaのレースカレンダー・レース結果ページから馬IDを自動収集するモジュール。

流れ:
  1. 指定した日付範囲でレース一覧ページを取得 → レースIDを抽出
  2. 各レース結果ページを取得 → 出走馬のnetkeiba_idを抽出
  3. DBに未登録の馬IDだけを返す（既登録かつ最近更新済みはスキップ）

これにより過去レースの全出走馬と、今後出走予定の馬を自動的に発見できる。
"""
import asyncio
import logging
import re
from datetime import date, timedelta

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..models import Horse
from .netkeiba import BASE_URL, HEADERS, DELAY

logger = logging.getLogger(__name__)

FRESH_DAYS = 7  # この日数以内に更新済みの馬は再スクレイプしない


async def _fetch_html(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        return resp.content.decode("EUC-JP", errors="replace")
    except Exception as e:
        logger.warning(f"fetch failed [{url}]: {e}")
        return None


async def get_race_ids_for_date(client: httpx.AsyncClient, target_date: date) -> list[str]:
    """指定日のレース一覧ページからレースIDを収集する。"""
    date_str = target_date.strftime("%Y%m%d")
    url = f"{BASE_URL}/?pid=race_list&date={date_str}"
    html = await _fetch_html(client, url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    race_ids = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"/race/(\d{12})/", a["href"])
        if m:
            race_ids.add(m.group(1))
    return list(race_ids)


async def get_horse_ids_from_race(client: httpx.AsyncClient, race_id: str) -> list[str]:
    """レース結果ページから出走馬のnetkeiba_idを収集する。"""
    url = f"{BASE_URL}/race/{race_id}/"
    html = await _fetch_html(client, url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    horse_ids = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"/horse/(\d{10})/", a["href"])
        if m:
            horse_ids.add(m.group(1))
    return list(horse_ids)


def _known_recent_ids(db: Session) -> set[str]:
    """最近更新済みの馬のnetkeiba_idセットを返す（スキップ対象）。"""
    from datetime import datetime, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=FRESH_DAYS)
    rows = (
        db.query(Horse.netkeiba_id)
        .filter(Horse.netkeiba_id.isnot(None))
        .filter(Horse.updated_at >= cutoff)
        .all()
    )
    return {r[0] for r in rows}


def _all_known_ids(db: Session) -> set[str]:
    """DBに登録済みの全netkeiba_idセットを返す。"""
    rows = db.query(Horse.netkeiba_id).filter(Horse.netkeiba_id.isnot(None)).all()
    return {r[0] for r in rows}


async def discover_horse_ids(
    db: Session,
    days_back: int = 14,
    days_forward: int = 14,
) -> list[str]:
    """
    過去 days_back 日〜未来 days_forward 日のレース情報から
    新規・未更新の馬IDリストを返す。

    - 既登録かつ FRESH_DAYS 以内に更新済みの馬はスキップ
    - 未登録の馬 or 長期間未更新の馬はリストに含める
    """
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days_back, 0, -1)]
    dates += [today + timedelta(days=i) for i in range(0, days_forward + 1)]

    skip_ids = _known_recent_ids(db)
    logger.info(f"スキップ対象（最近更新済み）: {len(skip_ids)}頭")

    collected_horse_ids: set[str] = set()

    async with httpx.AsyncClient() as client:
        # robots.txt チェック
        try:
            robots = await client.get(f"{BASE_URL}/robots.txt", headers=HEADERS, timeout=5.0)
            if "Disallow: /race/" in robots.text:
                logger.warning("robots.txt が /race/ を禁止しています — 発見スクレイプを中止")
                return []
        except Exception as e:
            logger.warning(f"robots.txt チェック失敗: {e}")

        for target_date in dates:
            race_ids = await get_race_ids_for_date(client, target_date)
            if not race_ids:
                await asyncio.sleep(DELAY)
                continue
            logger.info(f"{target_date}: {len(race_ids)}レースを発見")

            for race_id in race_ids:
                horse_ids = await get_horse_ids_from_race(client, race_id)
                new_ids = [hid for hid in horse_ids if hid not in skip_ids]
                collected_horse_ids.update(new_ids)
                await asyncio.sleep(DELAY)

            await asyncio.sleep(DELAY)

    result = list(collected_horse_ids)
    logger.info(f"新規スクレイプ対象: {len(result)}頭（スキップ: {len(skip_ids)}頭）")
    return result
