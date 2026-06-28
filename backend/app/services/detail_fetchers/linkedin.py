from .base import PlatformDetailFetcher

LINKEDIN = PlatformDetailFetcher(
    platform_id="linkedin",
    label="LinkedIn",
    url_keywords=["linkedin.com"],
    selectors=[".description__text", ".show-more-less-html__markup"],
)
