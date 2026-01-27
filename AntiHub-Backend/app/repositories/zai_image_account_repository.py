"""
ZAI Image 账号数据仓储

约定：
- Repository 层不负责 commit()，事务由调用方统一管理
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zai_image_account import ZaiImageAccount


class ZaiImageAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user_id(self, user_id: int) -> Sequence[ZaiImageAccount]:
        result = await self.db.execute(
            select(ZaiImageAccount)
            .where(ZaiImageAccount.user_id == user_id)
            .order_by(ZaiImageAccount.id.asc())
        )
        return result.scalars().all()

    async def list_enabled_by_user_id(self, user_id: int) -> Sequence[ZaiImageAccount]:
        result = await self.db.execute(
            select(ZaiImageAccount)
            .where(ZaiImageAccount.user_id == user_id, ZaiImageAccount.status == 1)
            .order_by(ZaiImageAccount.id.asc())
        )
        return result.scalars().all()

    async def get_by_id_and_user_id(self, account_id: int, user_id: int) -> Optional[ZaiImageAccount]:
        result = await self.db.execute(
            select(ZaiImageAccount).where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        account_name: str,
        credentials: str,
        status: int = 1,
    ) -> ZaiImageAccount:
        account = ZaiImageAccount(
            user_id=user_id,
            account_name=account_name,
            status=status,
            credentials=credentials,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def update_status(self, account_id: int, user_id: int, status: int) -> Optional[ZaiImageAccount]:
        await self.db.execute(
            update(ZaiImageAccount)
            .where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
            .values(status=status)
        )
        await self.db.flush()
        return await self.get_by_id_and_user_id(account_id, user_id)

    async def update_name(self, account_id: int, user_id: int, account_name: str) -> Optional[ZaiImageAccount]:
        await self.db.execute(
            update(ZaiImageAccount)
            .where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
            .values(account_name=account_name)
        )
        await self.db.flush()
        return await self.get_by_id_and_user_id(account_id, user_id)

    async def update_credentials(
        self,
        account_id: int,
        user_id: int,
        *,
        credentials: Optional[str] = None,
    ) -> Optional[ZaiImageAccount]:
        if credentials is None:
            return await self.get_by_id_and_user_id(account_id, user_id)

        await self.db.execute(
            update(ZaiImageAccount)
            .where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
            .values(credentials=credentials)
        )
        await self.db.flush()
        return await self.get_by_id_and_user_id(account_id, user_id)

    async def delete(self, account_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            delete(ZaiImageAccount).where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
        )
        await self.db.flush()
        return (result.rowcount or 0) > 0

    async def update_last_used_at(self, account_id: int, user_id: int) -> None:
        await self.db.execute(
            update(ZaiImageAccount)
            .where(
                ZaiImageAccount.id == account_id,
                ZaiImageAccount.user_id == user_id,
            )
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await self.db.flush()

