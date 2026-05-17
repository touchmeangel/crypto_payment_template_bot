from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

from  models.base import Base
from models.user import User
from models.session import Session
from models.filter import Filter
"""
Imports of these models are needed to correctly create tables in the database.
For more information see https://stackoverflow.com/questions/7478403/sqlalchemy-classes-across-files
"""

class Database:
  def __init__(self, db_url: str, echo: bool = True):
    self.db_url = db_url
    self.engine = create_async_engine(self.db_url, echo=echo)
    self.async_session_maker = async_sessionmaker(self.engine, class_=AsyncSession)

  async def check_all_tables_exist(self) -> bool:
    async with self.engine.begin() as conn:
      for table in Base.metadata.tables.values():
        result = await conn.execute(
          text(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :table_name)"
          ),
          {"table_name": table.name},
        )
        if not result.scalar():
          return False
    return True

  async def create_db_and_tables(self):
    async with self.engine.begin() as conn:
      if await self.check_all_tables_exist():
        logger.warning("All tables exist. Skipping creation.")
      else:
        logger.warning("Tables missing. Recreating database...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

  async def get_session(self) -> AsyncSession:
    return self.async_session_maker()

  async def close(self):
    await self.engine.dispose()

db = Database(DATABASE_URL, echo=False)