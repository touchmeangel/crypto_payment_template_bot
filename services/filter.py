import datetime
import math

from sqlalchemy import select, update, func
from db import db

import config

from models.filter import Filter
from language import LanguageService

class FilterService:
  @staticmethod
  async def is_exist(id: int) -> bool:
    async with db.async_session_maker() as session:
      stmt = select(Filter).where(Filter.id == id)
      is_exist = await session.execute(stmt)
      return is_exist.scalar() is not None

  @staticmethod
  async def get_by_id(id: int) -> Filter | None:
    async with db.async_session_maker() as session:
      stmt = select(Filter).where(Filter.id == id)
      filter_from_db = await session.execute(stmt)
      filter_from_db = filter_from_db.scalar()
      return filter_from_db
    
  @staticmethod
  async def set_status(id: int, status: bool):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        active=status)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_min_price(id: int, min_price: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        min_price=min_price)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_max_price(id: int, max_price: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        max_price=max_price)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_min_supply(id: int, min_supply: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        min_supply=min_supply)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_max_supply(id: int, max_supply: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        max_supply=max_supply)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_amount_stars(id: int, amount_stars: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        amount_stars=amount_stars)
      await session.execute(stmt)
      await session.commit()
  @staticmethod
  async def set_recipient_telegram_id(id: int, recipient_telegram_id: int):
    async with db.async_session_maker() as session:
      stmt = update(Filter).where(Filter.id == id).values(
        recipient_telegram_id=recipient_telegram_id)
      await session.execute(stmt)
      await session.commit()