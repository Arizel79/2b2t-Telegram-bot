import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    lang = Column(String, default='')
    state = Column(String, default='')
    first_use = Column(DateTime, default=datetime.now)
    requests = Column(Integer, default=0)
    configs = Column(String, default="{}")

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

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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
                print(f"Database error: {type(e)} - {e}")
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

