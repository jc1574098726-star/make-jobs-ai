from app.services.scrapers.boss_scraper import BossScraper
from app.services.scrapers.zhaopin_scraper import ZhaopinScraper
from app.services.scrapers.liepin_scraper import LiepinScraper
from app.services.scrapers.job51_scraper import Job51Scraper
from app.services.scrapers.yingjiesheng_scraper import YingjieshengScraper
from app.services.scrapers.linkedin_scraper import LinkedinScraper

SCRAPERS = {
    "boss": BossScraper,
    "zhaopin": ZhaopinScraper,
    "liepin": LiepinScraper,
    "51job": Job51Scraper,
    "yingjiesheng": YingjieshengScraper,
    "linkedin": LinkedinScraper,
}

__all__ = [
    "SCRAPERS",
    "BossScraper",
    "ZhaopinScraper",
    "LiepinScraper",
    "Job51Scraper",
    "YingjieshengScraper",
    "LinkedinScraper",
]
