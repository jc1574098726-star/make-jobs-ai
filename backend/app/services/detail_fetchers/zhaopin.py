from .base import PlatformDetailFetcher

ZHAOPIN = PlatformDetailFetcher(
    platform_id="zhaopin",
    label="智联招聘",
    url_keywords=["zhaopin.com"],
    selectors=[".describtion", ".job-summary"],
)
