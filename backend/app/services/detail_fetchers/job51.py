from .base import PlatformDetailFetcher

JOB51 = PlatformDetailFetcher(
    platform_id="51job",
    label="前程无忧",
    url_keywords=["51job.com", "qiancheng.com"],
    selectors=[".bmsg", ".tCompany_main"],
)
