"""
ZAI Image 服务

能力：
- ZAI Image 账号本地管理（token 加密存储）
- 对接 https://image.z.ai/api/proxy/images/generate 生成图片
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.zai_image_account_repository import ZaiImageAccountRepository
from app.utils.encryption import encrypt_api_key as encrypt_secret
from app.utils.encryption import decrypt_api_key as decrypt_secret

logger = logging.getLogger(__name__)


DEFAULT_RATIO = "16:9"
DEFAULT_RESOLUTION = "2K"

ALLOWED_RATIOS = {
    "1:1",
    "4:3",
    "3:2",
    "3:4",
    "1:4",
    "16:9",
    "9:16",
    "1:9",
    "21:9",
}

ALLOWED_RESOLUTIONS = {"1K", "2K"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_ratio(value: Any) -> str:
    ratio = _safe_str(value)
    if ratio in ALLOWED_RATIOS:
        return ratio
    return DEFAULT_RATIO


def _normalize_resolution(value: Any) -> str:
    res = _safe_str(value).upper()
    if res.endswith("K"):
        res = res[:-1] + "K"
    if res in ALLOWED_RESOLUTIONS:
        return res
    return DEFAULT_RESOLUTION


def _content_type_to_mime(value: Optional[str]) -> str:
    if not value:
        return "image/png"
    mime = value.split(";", 1)[0].strip()
    return mime or "image/png"


class ZaiImageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ZaiImageAccountRepository(db)
        self.settings = get_settings()

    @property
    def base_url(self) -> str:
        return (self.settings.zai_image_base_url or "https://image.z.ai").rstrip("/")

    @property
    def user_agent(self) -> str:
        return self.settings.zai_image_user_agent or "Mozilla/5.0 AppleWebKit/537.36 Chrome/143 Safari/537"

    async def list_accounts(self, user_id: int):
        return await self.repo.list_by_user_id(user_id)

    async def create_account(self, user_id: int, *, account_name: str, token: str):
        payload = {"token": _safe_str(token)}
        encrypted = encrypt_secret(json.dumps(payload, ensure_ascii=False))
        return await self.repo.create(
            user_id=user_id,
            account_name=_safe_str(account_name) or "ZAI Image Account",
            credentials=encrypted,
        )

    async def update_status(self, user_id: int, account_id: int, status: int):
        return await self.repo.update_status(account_id, user_id, status)

    async def update_name(self, user_id: int, account_id: int, account_name: str):
        return await self.repo.update_name(account_id, user_id, _safe_str(account_name))

    async def update_credentials(self, user_id: int, account_id: int, *, token: Optional[str]):
        credentials = None
        if token is not None:
            payload = {"token": _safe_str(token)}
            credentials = encrypt_secret(json.dumps(payload, ensure_ascii=False))
        return await self.repo.update_credentials(account_id, user_id, credentials=credentials)

    async def delete_account(self, user_id: int, account_id: int) -> bool:
        return await self.repo.delete(account_id, user_id)

    async def select_active_account(self, user_id: int):
        enabled: Sequence[Any] = await self.repo.list_enabled_by_user_id(user_id)
        if not enabled:
            raise ValueError("没有可用的 ZAI Image 账号，请先在账户管理中添加账号")
        return enabled[0]

    def _load_token(self, account) -> str:
        raw = decrypt_secret(account.credentials)
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {}
        return _safe_str(payload.get("token"))

    def _headers(self) -> Dict[str, str]:
        origin = self.base_url
        return {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Origin": origin,
            "Referer": f"{origin}/",
            "User-Agent": self.user_agent,
        }

    async def generate_image(
        self,
        *,
        account,
        prompt: str,
        ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        rm_label_watermark: bool = True,
    ) -> Dict[str, Any]:
        token = self._load_token(account)
        if not token:
            raise ValueError("账号缺少有效的 ZAI Token")

        prompt_text = _safe_str(prompt)
        if not prompt_text:
            raise ValueError("prompt 不能为空")

        payload = {
            "prompt": prompt_text,
            "ratio": _normalize_ratio(ratio),
            "resolution": _normalize_resolution(resolution),
            "rm_label_watermark": bool(rm_label_watermark),
        }

        url = f"{self.base_url}/api/proxy/images/generate"
        cookies = {"session": token}

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            resp = await client.post(url, json=payload, headers=self._headers(), cookies=cookies)

        try:
            data = resp.json()
        except Exception:
            data = None

        if resp.status_code >= 400:
            message = None
            if isinstance(data, dict):
                message = data.get("message") or data.get("detail") or data.get("error")
            message = message or resp.text
            raise ValueError(f"上游返回错误: {resp.status_code}: {message}")

        if not isinstance(data, dict):
            raise ValueError("上游返回了非 JSON 响应")

        code = int(data.get("code") or 0)
        if code != 200:
            raise ValueError(str(data.get("message") or data))

        image = (data.get("data") or {}).get("image") or {}
        if not isinstance(image, dict):
            image = {}

        image_url = _safe_str(image.get("image_url") or image.get("imageUrl"))
        if not image_url:
            raise ValueError("上游未返回 image_url")

        try:
            await self.repo.update_last_used_at(account.id, account.user_id)
        except Exception as e:
            logger.warning("update_last_used_at failed: %s", str(e))

        return {
            "image_id": _safe_str(image.get("image_id") or image.get("imageId")),
            "image_url": image_url,
            "width": image.get("width"),
            "height": image.get("height"),
            "ratio": _safe_str(image.get("ratio")) or payload["ratio"],
            "resolution": _safe_str(image.get("resolution")) or payload["resolution"],
            "created_at": _safe_str(image.get("created_at") or image.get("createdAt")),
        }

    async def fetch_image_bytes(self, url: str) -> Tuple[bytes, str]:
        image_url = _safe_str(url)
        if not image_url:
            raise ValueError("image_url 不能为空")

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            mime = _content_type_to_mime(resp.headers.get("Content-Type"))
            return resp.content, mime

    async def fetch_image_base64(self, url: str) -> Tuple[str, str]:
        content, mime = await self.fetch_image_bytes(url)
        return base64.b64encode(content).decode("ascii"), mime
