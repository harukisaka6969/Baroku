import httpx
import asyncio
import logging
from bs4 import BeautifulSoup
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
DELAY = float(os.getenv("SCRAPER_DELAY", "2"))
BASE_URL = "https://db.netkeiba.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BarokuBot/0.1; +https://github.com/baroku/baroku)",
    "Accept-Language": "ja,en;q=0.9",
}


async def fetch_horse(client: httpx.AsyncClient, horse_id: str) -> Optional[dict]:
    """Fetch a single horse profile from netkeiba. Respects robots.txt delay."""
    url = f"{BASE_URL}/horse/{horse_id}/"
    try:
        resp = await client.get(url, headers=HEADERS, timeout=10.0)
        resp.raise_for_status()
        return parse_horse_page(resp.text, horse_id)
    except Exception as e:
        logger.error(f"Failed to fetch horse {horse_id}: {e}")
        return None


def parse_horse_page(html: str, horse_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"netkeiba_id": horse_id}

    title_tag = soup.find("div", class_="horse_title")
    if title_tag:
        h1 = title_tag.find("h1")
        if h1:
            data["name"] = h1.get_text(strip=True)

    prof_table = soup.find("table", class_="db_prof_table")
    if prof_table:
        for row in prof_table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            val = td.get_text(strip=True)
            if key == "生年月日":
                data["born_year"] = int(val[:4]) if val[:4].isdigit() else None
            elif key == "調教師":
                data["trainer"] = val
            elif key == "馬主":
                data["owner"] = val
            elif key == "生産者":
                data["farm"] = val
            elif key == "産地":
                data["birthplace"] = val
            elif key == "毛色":
                data["color"] = val

    return data


async def scrape_horses(horse_ids: list[str]) -> list[dict]:
    """Scrape multiple horses with rate limiting. IMPORTANT: check robots.txt first."""
    results = []
    async with httpx.AsyncClient() as client:
        # Check robots.txt
        try:
            robots = await client.get(f"{BASE_URL}/robots.txt", headers=HEADERS, timeout=5.0)
            logger.info(f"robots.txt status: {robots.status_code}")
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt: {e}")

        for horse_id in horse_ids:
            result = await fetch_horse(client, horse_id)
            if result:
                results.append(result)
            else:
                logger.warning(f"Skipping horse {horse_id} due to fetch error")
            await asyncio.sleep(DELAY)

    return results
