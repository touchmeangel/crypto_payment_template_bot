from aiogram import types
from aiogram.filters import BaseFilter
from services.user import UserService

from config import ADMIN_ID_LIST

class AdminIdFilter(BaseFilter):
    async def __call__(self, message: types.Message):
        return message.from_user.id in ADMIN_ID_LIST
    
class IsUserExistFilter(BaseFilter):
  async def __call__(self, message: types.Message):
      return await UserService.is_exist(message.from_user.id)

class UserSubscriptionValidFilter(BaseFilter):
  async def __call__(self, message: types.Message):
      return await UserService.is_subscription_valid(message.from_user.id)