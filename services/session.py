import datetime
import math

from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from db import db

import config

from models.session import Session
from models.filter import Filter
from language import LanguageService

class SessionService:
  @staticmethod
  async def is_exist(id: int) -> bool:
    async with db.async_session_maker() as session:
      stmt = select(Session).where(Session.id == id)
      is_exist = await session.execute(stmt)
      return is_exist.scalar() is not None

  @staticmethod
  async def get_by_id(id: int) -> Session | None:
    async with db.async_session_maker() as session:
      stmt = select(Session).where(Session.id == id)
      session_from_db = await session.execute(stmt)
      session_from_db = session_from_db.scalar()
      return session_from_db
  
  @staticmethod
  async def is_active(id: int) -> bool:
    async with db.async_session_maker() as session:
      stmt = select(Filter).where(Filter.session_id == id).where(Filter.active == True)
      filter_from_db = await session.execute(stmt)
      filter_from_db = filter_from_db.first()

      return filter_from_db is not None
    
  @staticmethod
  async def add_filter(id: int, recipient_tg_id: int, min_price: int = 0, max_price: int = -1, min_supply: int = 0, max_supply: int = -1, amount_stars: int = -1) -> int | None:
    async with db.async_session_maker() as session:
      stmt = (
        select(Session)
        .where(Session.id == id)
        .options(selectinload(Session.user))
      )
      query = await session.execute(stmt)
      user_session = query.scalar()
      if user_session is None:
        return
      
      new_filter = Filter(
        recipient_telegram_id=recipient_tg_id,
        min_price=min_price,
        max_price=max_price,
        min_supply=min_supply,
        max_supply=max_supply,
        amount_stars=amount_stars,
      )

      user_session.filters.append(new_filter)
      session.add(new_filter)

      await session.flush()
      await session.refresh(new_filter)
      new_filter_id = new_filter.id
      await session.commit()
      return new_filter_id
    
  @staticmethod
  async def remove_filter(session_id: int, filter_id: int):
    async with db.async_session_maker() as session:
      result = await session.execute(
        select(Session)
          .where(Session.id == session_id)
          .options(selectinload(Session.filters))
      )
      s = result.scalar_one_or_none()
      if s is None:
        return False
      
      target = next((f for f in s.filters if f.id == filter_id), None)
      if not target:
        return False
      
      s.filters.remove(target)

      await session.commit()
      return True

  @staticmethod
  async def filters_amount(id: int) -> int:
    async with db.async_session_maker() as session:
      stmt = select(func.count(Filter.id))\
        .join(Filter.session)\
        .where(Session.id == id)
      filter_count = await session.execute(stmt)
      filter_count = filter_count.scalar_one()
      return filter_count
    
  @staticmethod
  async def new_filter_available(id: int) -> bool:
    a = await SessionService.filters_amount(id)
    return a < 5