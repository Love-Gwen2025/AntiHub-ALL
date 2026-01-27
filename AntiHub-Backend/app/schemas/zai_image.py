"""
ZAI Image 账号相关的数据模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ZaiImageAccountCreateRequest(BaseModel):
    account_name: str = Field(..., description="账号名称")
    token: str = Field(..., description="ZAI Token（Cookie session）")


class ZaiImageAccountUpdateStatusRequest(BaseModel):
    status: int = Field(..., description="0=禁用，1=启用")


class ZaiImageAccountUpdateNameRequest(BaseModel):
    account_name: str = Field(..., description="账号名称")


class ZaiImageAccountUpdateCredentialsRequest(BaseModel):
    token: Optional[str] = Field(None, description="ZAI Token（留空不修改）")


class ZaiImageAccountResponse(BaseModel):
    account_id: int = Field(..., alias="id")
    account_name: str
    status: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}

