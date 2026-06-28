from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import BASE_DIR

router = APIRouter(prefix="/settings", tags=["settings"])

USER_SETTINGS_PATH = BASE_DIR / "data" / "user_settings.json"


class ApiSettingsInput(BaseModel):
    provider: str = "anthropic"
    api_base_url: str = ""
    api_key: str = ""
    model: str = ""


class ApiSettingsView(BaseModel):
    provider: str
    api_base_url: str
    api_key_masked: str
    model: str
    configured: bool


class ModelTestRequest(BaseModel):
    provider: str = "anthropic"
    api_base_url: str = ""
    api_key: str = ""
    model: str = ""


def _load() -> Dict:
    if USER_SETTINGS_PATH.exists():
        try:
            return json.loads(USER_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save(data: Dict) -> None:
    USER_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USER_SETTINGS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_user_api_key() -> Optional[str]:
    settings = _load()
    return settings.get("api_key") or None


def get_user_api_base_url() -> Optional[str]:
    settings = _load()
    return settings.get("api_base_url") or None


def get_user_model() -> Optional[str]:
    settings = _load()
    return settings.get("model") or None


def get_user_provider() -> str:
    settings = _load()
    return settings.get("provider") or "anthropic"


def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("/providers")
def list_providers() -> Dict:
    from app.services.providers import get_all_providers
    return get_all_providers()


@router.get("", response_model=ApiSettingsView)
def get_settings() -> ApiSettingsView:
    data = _load()
    api_key = data.get("api_key", "")
    return ApiSettingsView(
        provider=data.get("provider", "anthropic"),
        api_base_url=data.get("api_base_url", ""),
        api_key_masked=_mask_key(api_key),
        model=data.get("model", ""),
        configured=bool(api_key),
    )


@router.put("", response_model=ApiSettingsView)
def update_settings(payload: ApiSettingsInput) -> ApiSettingsView:
    data = _load()
    data["provider"] = payload.provider
    data["api_base_url"] = payload.api_base_url
    # 只有当用户输入了真实密钥（不是掩码）时才更新
    if payload.api_key and payload.api_key != "••••••••":
        data["api_key"] = payload.api_key
    if payload.model:
        data["model"] = payload.model
    _save(data)

    from app.services.claude_service import ClaudeService
    ClaudeService.reinit()

    return ApiSettingsView(
        provider=data.get("provider", "anthropic"),
        api_base_url=data.get("api_base_url", ""),
        api_key_masked=_mask_key(data.get("api_key", "")),
        model=data.get("model", ""),
        configured=bool(data.get("api_key")),
    )


@router.post("/test")
def test_connection(payload: ModelTestRequest) -> Dict:
    # 如果收到的是掩码，则使用已保存的密钥
    api_key = payload.api_key
    if not api_key or api_key == "••••••••" or api_key == "********":
        saved_key = get_user_api_key()
        if saved_key:
            api_key = saved_key

    if not api_key:
        raise HTTPException(status_code=400, detail="API 密钥不能为空")

    from app.services.providers import get_provider
    try:
        provider = get_provider(payload.provider)
    except KeyError:
        raise HTTPException(status_code=400, detail="未知的 API 提供商: {}".format(payload.provider))

    base_url = payload.api_base_url or provider["base_url"]
    api_format = provider["api_format"]

    if api_format == "openai":
        return _test_openai(api_key, base_url, payload.model, provider)
    else:
        return _test_anthropic(api_key, base_url, payload.model, provider)


def _test_openai(api_key: str, base_url: str, model: str, provider: Dict) -> Dict:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        models = []
        try:
            resp = client.models.list()
            for m in resp.data:
                if m.id:
                    models.append(m.id)
            models.sort()
        except Exception:
            pass

        if not models:
            test_model = model or provider["models"][0] if provider.get("models") else "gpt-4o-mini"
            client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            models = provider.get("models", [])

        return {"success": True, "models": models}
    except openai.AuthenticationError:
        raise HTTPException(status_code=400, detail="API 密钥无效，请检查后重试")
    except Exception as exc:
        msg = str(exc)
        # HTML 404 from proxy/gateway means base URL is wrong
        if "<html" in msg.lower() and "404" in msg:
            raise HTTPException(status_code=400, detail="API 地址无法访问（404），请检查地址是否正确")
        if "Not supported model" in msg or "model_not_found" in msg:
            return {
                "success": True,
                "models": provider.get("models", []),
                "hint": "代理未返回模型列表，已显示常用模型。如模型名不同，请手动输入。",
            }
        raise HTTPException(status_code=400, detail="API 连接失败：{}".format(msg[:200]))


def _test_anthropic(api_key: str, base_url: str, model: str, provider: Dict) -> Dict:
    models = _try_fetch_models(base_url, api_key)
    if models:
        return {"success": True, "models": models}

    try:
        import anthropic
        kwargs = {"api_key": api_key}
        if base_url and base_url != "https://api.anthropic.com":
            kwargs["base_url"] = base_url
        client = anthropic.Anthropic(**kwargs)
        client.messages.create(
            model=model or "claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {"success": True, "models": provider.get("models", [])}
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=400, detail="API 密钥无效，请检查后重试")
    except Exception as exc:
        msg = str(exc)
        if "404" in msg or "Not supported model" in msg:
            return {
                "success": True,
                "models": provider.get("models", []),
                "hint": "代理未返回模型列表，已显示常用模型。如模型名不同，请手动输入。",
            }
        raise HTTPException(status_code=400, detail="API 连接失败：{}".format(msg[:200]))


def _try_fetch_models(base_url: str, api_key: str) -> List[str]:
    try:
        import httpx
        url = base_url.rstrip("/") + "/v1/models"
        resp = httpx.get(url, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            models = []
            for item in data.get("data", []):
                mid = item.get("id", "")
                if mid:
                    models.append(mid)
            if models:
                models.sort()
                return models
    except Exception:
        pass
    return []
