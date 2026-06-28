from __future__ import annotations

from typing import Dict

from .base import PlatformDetailFetcher
from .boss import BOSS
from .generic import GENERIC
from .job51 import JOB51
from .liepin import LIEPIN
from .linkedin import LINKEDIN
from .yingjiesheng import YINGJIESHENG
from .zhaopin import ZHAOPIN

_FETCHERS: Dict[str, PlatformDetailFetcher] = {
    f.platform_id: f
    for f in [LIEPIN, BOSS, ZHAOPIN, JOB51, LINKEDIN, YINGJIESHENG, GENERIC]
}


def detect_fetcher(url: str) -> PlatformDetailFetcher:
    """根据 URL 检测平台，返回对应配置。"""
    u = url.lower()
    for fid, fetcher in _FETCHERS.items():
        if fid == "generic":
            continue
        if any(kw in u for kw in fetcher.url_keywords):
            return fetcher
    return GENERIC


def get_fetcher(platform_id: str) -> PlatformDetailFetcher:
    return _FETCHERS.get(platform_id, GENERIC)
