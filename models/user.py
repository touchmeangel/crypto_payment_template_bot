from sqlalchemy import Column, Integer, DateTime, String, Boolean, Float, func, ForeignKey
from sqlalchemy.orm import relationship, backref

from language import LanguageService
from models.base import Base, I128


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_username = Column(String, unique=True)
    telegram_id = Column(I128, nullable=False)
    registered_at = Column(DateTime, default=func.now())
    can_receive_messages = Column(Boolean, default=True)
    language = Column(String, default=LanguageService.get_default_code())
    subscription_expires = Column(DateTime(timezone=True), default=None)