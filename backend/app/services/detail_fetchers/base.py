from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PlatformDetailFetcher:
    """某平台的详情页抓取配置。"""
    platform_id: str
    label: str
    url_keywords: List[str] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)
    force_playwright: bool = False
    use_body_text: bool = False
    noise_patterns: List[str] = field(default_factory=list)
    post_processor: Optional[str] = None
