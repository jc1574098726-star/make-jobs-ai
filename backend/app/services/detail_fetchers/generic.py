from .base import PlatformDetailFetcher

GENERIC = PlatformDetailFetcher(
    platform_id="generic",
    label="通用",
    url_keywords=[],
    selectors=["article", "main", "[role='main']"],
)
