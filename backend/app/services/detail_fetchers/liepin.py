from .base import PlatformDetailFetcher

LIEPIN = PlatformDetailFetcher(
    platform_id="liepin",
    label="猎聘",
    url_keywords=["liepin.com"],
    selectors=[".job-intro-content", ".job-intro__content", ".job-qualifications", ".job-header"],
    use_body_text=True,
)
