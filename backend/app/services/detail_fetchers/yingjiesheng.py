from .base import PlatformDetailFetcher

YINGJIESHENG = PlatformDetailFetcher(
    platform_id="yingjiesheng",
    label="应届生",
    url_keywords=["yingjiesheng.com"],
    selectors=[".job-detail", ".job-info"],
)
