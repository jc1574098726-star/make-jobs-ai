from .base import PlatformDetailFetcher

BOSS = PlatformDetailFetcher(
    platform_id="boss",
    label="BOSS直聘",
    url_keywords=["zhipin.com"],
    selectors=[".job-detail-section", ".job-sec-text"],
    force_playwright=True,
)
