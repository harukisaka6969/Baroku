"""
CLI runner for the netkeiba scraper.
Usage: python -m app.scraper.run_scraper <horse_id1> [horse_id2 ...]

IMPORTANT: This scraper is for prototype/research use only.
- Always verify robots.txt compliance before running
- Minimum 2-second delay between requests (enforced)
- For commercial use, migrate to JRA-VAN data service
"""
import asyncio
import sys
import logging
from .netkeiba import scrape_horses

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(horse_ids: list[str]):
    logger.info(f"Starting scrape for {len(horse_ids)} horse(s)")
    results = await scrape_horses(horse_ids)
    logger.info(f"Scraped {len(results)} horse(s) successfully")
    for r in results:
        logger.info(r)
    return results


if __name__ == "__main__":
    ids = sys.argv[1:] if len(sys.argv) > 1 else []
    if not ids:
        print("Usage: python -m app.scraper.run_scraper <horse_id1> [horse_id2 ...]")
        sys.exit(1)
    asyncio.run(main(ids))
