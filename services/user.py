import datetime
import math

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from db import db

from models.user import User
from models.session import Session
from language import LanguageService

class UserService:
    users_per_page = 20

    @staticmethod
    async def is_exist(telegram_id: int) -> bool:
        async with db.async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            is_exist = await session.execute(stmt)
            return is_exist.scalar() is not None

    @staticmethod
    async def get_next_user_id() -> int:
        async with db.async_session_maker() as session:
            query = select(User.id).order_by(User.id.desc()).limit(1)
            last_user_id = await session.execute(query)
            last_user_id = last_user_id.scalar()
            if last_user_id is None:
                return 0
            else:
                return int(last_user_id) + 1

    @staticmethod
    async def create(telegram_id: int, telegram_username: str):
        async with db.async_session_maker() as session:
            next_user_id = await UserService.get_next_user_id()
            new_user = User(
                id=next_user_id,
                telegram_username=telegram_username,
                telegram_id=telegram_id,
            )
            session.add(new_user)
            await session.commit()

    @staticmethod
    async def user_logged(telegram_id: int, telegram_username: str):
        is_exist = await UserService.is_exist(telegram_id)
        if is_exist is False:
            await UserService.create(telegram_id, telegram_username)
        else:
            await UserService.update_receive_messages(telegram_id, True)
            await UserService.update_username(telegram_id, telegram_username)

    @staticmethod
    async def update_username(telegram_id: int, telegram_username: str):
        async with db.async_session_maker() as session:
            user_from_db = await UserService.get_by_tgid(telegram_id)
            if user_from_db and user_from_db.telegram_username != telegram_username:
                stmt = update(User).where(User.telegram_id == telegram_id).values(telegram_username=telegram_username)
                await session.execute(stmt)
                await session.commit()

    @staticmethod
    async def get_by_tgid(telegram_id: int) -> User | None:
        async with db.async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            user_from_db = await session.execute(stmt)
            user_from_db = user_from_db.scalar()
            return user_from_db

    @staticmethod
    async def get_by_id(id: int) -> User:
        async with db.async_session_maker() as session:
            stmt = select(User).where(User.id == id)
            user_from_db = await session.execute(stmt)
            user_from_db = user_from_db.scalar()
            return user_from_db

    @staticmethod
    async def update_language(telegram_id: int, language_code):
        async with db.async_session_maker() as session:
            user_from_db = await UserService.get_by_tgid(telegram_id)
            if user_from_db and user_from_db.language != language_code:
                stmt = update(User).where(User.telegram_id == telegram_id).values(language=language_code)
                await session.execute(stmt)
                await session.commit()

    @staticmethod
    async def get_users_tg_ids_for_sending():
        async with db.async_session_maker() as session:
            stmt = select(User.telegram_id).where(User.can_receive_messages == True)
            user_ids = await session.execute(stmt)
            user_ids = user_ids.scalars().all()
            return user_ids

    @staticmethod
    async def get_all_users_count():
        async with db.async_session_maker() as session:
            stmt = func.count(User.id)
            users_count = await session.execute(stmt)
            return users_count.scalar()

    @staticmethod
    async def get_new_users_by_timedelta(timedelta_int, page):
        async with db.async_session_maker() as session:
            current_time = datetime.datetime.now()
            one_day_interval = datetime.timedelta(days=int(timedelta_int))
            time_to_subtract = current_time - one_day_interval
            stmt = select(User).where(User.registered_at >= time_to_subtract, User.telegram_username != None).limit(
                UserService.users_per_page).offset(
                page * UserService.users_per_page)
            count_stmt = select(func.count(User.id)).where(User.registered_at >= time_to_subtract)
            users = await session.execute(stmt)
            users_count = await session.execute(count_stmt)
            return users.scalars().all(), users_count.scalar_one()

    @staticmethod
    async def get_max_page_for_users_by_timedelta(timedelta_int):
        async with db.async_session_maker() as session:
            current_time = datetime.datetime.now()
            one_day_interval = datetime.timedelta(days=int(timedelta_int))
            time_to_subtract = current_time - one_day_interval
            stmt = select(func.count(User.id)).where(User.registered_at >= time_to_subtract,
                                                     User.telegram_username != None)
            users = await session.execute(stmt)
            users = users.scalar_one()
            if users % UserService.users_per_page == 0:
                return users / UserService.users_per_page - 1
            else:
                return math.trunc(users / UserService.users_per_page)

    @staticmethod
    async def update_receive_messages(telegram_id, new_value):
        async with db.async_session_maker() as session:
            stmt = update(User).where(User.telegram_id == telegram_id).values(
                can_receive_messages=new_value)
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_language_code(telegram_id):
        user = await UserService.get_by_tgid(telegram_id)
        if user is None:
            return LanguageService.get_default_code()
        return user.language
    
    @staticmethod
    async def sessions_amount(telegram_id: int) -> int:
      async with db.async_session_maker() as session:
        stmt = select(func.count(Session.id))\
          .join(Session.user)\
          .where(User.telegram_id == telegram_id)
        session_count = await session.execute(stmt)
        session_count = session_count.scalar_one()
        return session_count

    @staticmethod
    async def new_session_available(telegram_id: int) -> bool:
      a = await UserService.sessions_amount(telegram_id)
      return a < 3
    
    @staticmethod
    async def subscribe_user_for_3_months(telegram_id: int) -> bool:
      async with db.async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return False

        now = datetime.datetime.now(datetime.timezone.utc)
        new_expiry = now + relativedelta(months=3)
        user.subscription_expires = new_expiry

        session.add(user)
        await session.commit()
        return True

    @staticmethod
    async def is_subscription_valid(telegram_id: int) -> bool:
      async with db.async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        query = await session.execute(stmt)
        user = query.scalar()
        if user is None:
          return False
        
        return user.subscription_expires and user.subscription_expires > datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    async def subscription_expiration_date(telegram_id: int) -> datetime.datetime | None:
      async with db.async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        query = await session.execute(stmt)
        user = query.scalar()
        if user is None:
          return None
        
        return user.subscription_expires

    @staticmethod
    async def add_session(telegram_id: int, api_id: int, api_hash: str, session_string: str):
      async with db.async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        query = await session.execute(stmt)
        user = query.scalar()
        if user is None:
          return
        
        user.sessions.append(Session(session_string=session_string, api_id=api_id, api_hash=api_hash))
        await session.commit()

    @staticmethod
    async def remove_session(telegram_id: int, session_id: int):
      async with db.async_session_maker() as session:
        result = await session.execute(
          select(User)
            .where(User.telegram_id == telegram_id)
            .options(selectinload(User.sessions))
        )
        user = result.scalar_one_or_none()
        if user is None:
          return False
        
        target = next((s for s in user.sessions if s.id == session_id), None)
        if not target:
          return False
        
        user.sessions.remove(target)

        await session.commit()
        return True