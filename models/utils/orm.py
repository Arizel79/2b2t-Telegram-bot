import json
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from models.utils.utils import *
from aiogram.types import Message, InlineQuery, CallbackQuery
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, default='')
    name = Column(String, default='')
    lang = Column(String, default='')
    state = Column(String, default='')
    first_use = Column(DateTime, default=datetime.now)
    requests = Column(Integer, default=0)
    configs = Column(String, default="{}")

class PlayerTracking(Base):
    __tablename__ = 'players_tracking'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default='', nullable=False)
    player_username = Column(String, default="")
    player_uuid = Column(String, default="")
    is_active = Column(Boolean, default=True)
    notify_messages = Column(Boolean, default=True)
    notify_connections = Column(Boolean, default=True)
    notify_deaths = Column(Integer, default=True)
    notify_kills = Column(Integer, default=True)
    importance = Column(Integer, default=1) # 0 - without notify; 1 - with notify; 2 - notifu with @mention
    created_at = Column(DateTime, default=datetime.now)


class SavedState(Base):
    __tablename__ = 'saved'

    id = Column(Integer, primary_key=True)
    data = Column(String, default='{}')


class AsyncDatabaseSession:
    def __init__(self, db_url='sqlite+aiosqlite:///2b2t_bot_data.sqlite'):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.logger = setup_logger("orm", "orm.log", logging.INFO)

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.debug("database created")

    async def update_credentials(self, event: Message | CallbackQuery) -> None:
        # Извлекаем пользователя из события
        user_from_event = event.from_user
        user_id = user_from_event.id
        username = f"@{user_from_event.username}" if user_from_event.username else None
        name = user_from_event.full_name

        async with self.async_session() as session:
            # Пытаемся получить пользователя из БД
            user = await session.get(User, user_id)

            if user:
                # Обновляем данные существующего пользователя
                user.username = username
                user.name = name
            else:
                # Создаем нового пользователя
                new_user = User(
                    id=user_id,
                    username=username,
                    name=name
                )
                session.add(new_user)

            # Сохраняем изменения в БД
            await session.commit()
    # Tracking методы
    async def add_player_tracking(self, user_id: int, player_username: str, player_uuid: str,
                                  notify_messages=True, notify_connections=True,
                                  notify_deaths=True, notify_kills=True, importance=1):
        async with self.async_session() as session:
            tracking = PlayerTracking(
                user_id=user_id,
                player_username=player_username,
                player_uuid=player_uuid,
                notify_messages=notify_messages,
                notify_connections=notify_connections,
                notify_deaths=notify_deaths,
                notify_kills=notify_kills,
                importance=importance
            )
            session.add(tracking)
            await session.commit()
            return tracking.id

    async def get_player_tracking(self, user_id: int, player_username: str = None, player_uuid: str = None):
        async with self.async_session() as session:
            stmt = select(PlayerTracking).where(PlayerTracking.user_id == user_id)

            if player_username:
                stmt = stmt.where(PlayerTracking.player_username == player_username)
            if player_uuid:
                stmt = stmt.where(PlayerTracking.player_uuid == player_uuid)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_tracking_for_player(self, player_username: str = None, player_uuid: str = None):
        async with self.async_session() as session:
            stmt = select(PlayerTracking).where(PlayerTracking.is_active == True)

            if player_username:
                stmt = stmt.where(PlayerTracking.player_username == player_username)
            if player_uuid:
                stmt = stmt.where(PlayerTracking.player_uuid == player_uuid)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def update_player_tracking(self, tracking_id: int, **kwargs):
        async with self.async_session() as session:
            tracking = await session.get(PlayerTracking, tracking_id)
            if tracking:
                for key, value in kwargs.items():
                    if hasattr(tracking, key):
                        setattr(tracking, key, value)
                await session.commit()
                return True
            return False

    async def delete_player_tracking(self, tracking_id: int):
        async with self.async_session() as session:
            tracking = await session.get(PlayerTracking, tracking_id)
            if tracking:
                await session.delete(tracking)
                await session.commit()
                return True
            return False

    async def get_user_trackings(self, user_id: int):
        async with self.async_session() as session:
            stmt = select(PlayerTracking).where(
                PlayerTracking.user_id == user_id
            ).order_by(PlayerTracking.created_at.desc())

            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_tracking_by_id(self, tracking_id: int, user_id: int = None):
        async with self.async_session() as session:
            stmt = select(PlayerTracking).where(PlayerTracking.id == tracking_id)

            if user_id:
                stmt = stmt.where(PlayerTracking.user_id == user_id)

            result = await session.execute(stmt)
            return result.scalar()

    async def get_user(self, user_id: int) -> User:
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                user = User(id=user_id)
                session.add(user)
                await session.commit()
            return user

    async def get_saved_state(self, state_id: int) -> SavedState:
        async with self.async_session() as session:
            saved_state = await session.get(SavedState, state_id)
            return json.loads(saved_state.data)

    async def add_saved_state(self, data: dict) -> int:
        async with self.async_session() as session:
            try:
                saved_state = SavedState(data=json.dumps(data))
                session.add(saved_state)
                await session.flush()
                await session.commit()
                return saved_state.id

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database error: {type(e)} - {e}")
                self.logger.exception(e)
                raise

    async def update_saved_state(self, state_id: int, data: dict):
        async with self.async_session() as session:
            saved_state = await session.get(SavedState, state_id)
            if saved_state:
                saved_state.data = json.dumps(data)
                await session.commit()
                return True
            return False

    async def check_user_found(self, user_id: int):
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            return user

    async def update_lang(self, user_id: int, lang: str):
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.lang = lang
                await session.commit()

    async def update_configs(self, user_id: int, configs: str):
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.configs = configs
                await session.commit()

    async def increment_requests(self, user_id: int, max_retries: int = 3):
        retry_count = 0
        while retry_count < max_retries:
            try:
                async with self.async_session() as session:
                    user = await session.get(User, user_id)
                    if user:
                        user.requests += 1
                        await session.commit()
                        return True
                    return False
            except (OperationalError, SQLAlchemyError) as e:
                if "locked" in str(e) and retry_count < max_retries - 1:
                    retry_count += 1
                    await asyncio.sleep(0.1 * retry_count)  # Экспоненциальная задержка
                    continue
                raise
        return False

    async def get_user_stats(self, user_id: int) -> dict:
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                return {}
            if user:
                return {
                    'id': user.id,
                    'lang': user.lang,
                    'first_use': user.first_use,
                    'requests': user.requests,
                    "configs": json.loads(user.configs)
                }
            return {}

    async def is_user_select_lang(self, user_id: int):
        async with self.async_session() as session:
            stats = await self.get_user_stats(user_id)
            if stats.get("lang", "") == "":
                return False
            return True


if __name__ == '__main__':
    import asyncio
    db = AsyncDatabaseSession()
    async def main():
        db = AsyncDatabaseSession()
        await db.create_all()
        try:
            state_id = await db.add_saved_state({"key": "value"})
            print(f"Success! ID: {state_id}")
        except Exception as e:
            print(f"Failed: {e}")
    asyncio.run(main())

