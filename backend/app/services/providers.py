from __future__ import annotations

from typing import Dict, List


PROVIDERS = {
    "anthropic": {
        "name": "Anthropic (Claude)",
        "base_url": "https://api.anthropic.com",
        "api_format": "anthropic",
        "models": [
            "claude-opus-4-7",
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
        ],
    },
    "openai": {
        "name": "ChatGPT (OpenAI)",
        "base_url": "https://api.openai.com",
        "api_format": "openai",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "api_format": "openai",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "api_format": "openai",
        "models": [
            "Qwen/Qwen2.5-72B-Instruct",
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Pro/deepseek-ai/DeepSeek-R1",
        ],
    },
    "mimo": {
        "name": "小米 MiMo",
        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "api_format": "openai",
        "models": [
            "mimo-v2.5-pro",
            "mimo-v2.5",
            "mimo-v2-pro",
            "mimo-v2-omni",
        ],
    },
    "volcano": {
        "name": "火山引擎 (ByteDance)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_format": "openai",
        "models": ["doubao-pro-32k", "doubao-pro-128k", "doubao-lite-32k"],
    },
    "nvidia": {
        "name": "NVIDIA",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_format": "openai",
        "models": [
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-70b-instruct",
            "deepseek-ai/deepseek-r1",
        ],
    },
    "zhipu": {
        "name": "智谱 (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_format": "openai",
        "models": ["glm-4", "glm-4-flash", "glm-4-plus", "glm-4-long"],
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.chat/v1",
        "api_format": "openai",
        "models": ["abab6.5s-chat", "abab7-chat"],
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "base_url": "https://api.moonshot.cn/v1",
        "api_format": "openai",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    },
    "stepfun": {
        "name": "StepFun (阶跃星辰)",
        "base_url": "https://api.stepfun.com/v1",
        "api_format": "openai",
        "models": ["step-1-8k", "step-1-32k", "step-1-128k"],
    },
    "qwen": {
        "name": "千问 (阿里云)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_format": "openai",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_format": "openai",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "api_format": "openai",
        "models": [],
    },
}  # type: Dict[str, Dict[str, object]]


def get_provider(provider_id: str) -> Dict[str, object]:
    if provider_id not in PROVIDERS:
        raise KeyError("Unknown provider: {}".format(provider_id))
    return PROVIDERS[provider_id]


def get_all_providers() -> Dict[str, Dict[str, object]]:
    return PROVIDERS
