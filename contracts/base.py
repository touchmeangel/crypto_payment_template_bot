from aiohttp.client_exceptions import ClientResponseError
from web3 import AsyncWeb3, AsyncHTTPProvider
from utils.retry import retry_on_429
from functools import wraps
import aiofiles
import asyncio
import logging
import json
import time
import os

logger = logging.getLogger(__name__)

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ZERO_SIGNATURE = "0xb8464ee39aaf781c640e004d9e5c070935744844f5aa24285355ff345b8a21b83b4fdc930e0eb79a6b771d75b98a9b1dadaf91e7d633449575197a81b831f6e31b"

class Base:
  _instances: dict[str, "Base"] = {}

  def __new__(cls, rpc: str):
    if rpc not in cls._instances:
      instance = super().__new__(cls)
      cls._instances[rpc] = instance
      instance._init(rpc)
    return cls._instances[rpc]

  def _init(self, rpc: str):
    self.web3 = AsyncWeb3(AsyncHTTPProvider(rpc))

  def _deadline(self) -> int:
    return int(time.time()) + 10 * 60
  
  @retry_on_429()
  async def _block_at_timestamp(self, target_timestamp: int) -> int:
    current_block = await self.web3.eth.block_number
    current_timestamp = (await self.web3.eth.get_block(current_block)).timestamp

    if target_timestamp > current_timestamp:
      raise ValueError("Target timestamp is in the future")

    low, high = 0, current_block

    while low < high:
      mid = (low + high) // 2
      mid_timestamp = (await self.web3.eth.get_block(mid)).timestamp
      if mid_timestamp < target_timestamp:
        low = mid + 1
      else:
        high = mid

    return low

  async def load_abi(self, name: str) -> str:
    path = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/"
    async with aiofiles.open(os.path.abspath(path + f"{name}.abi")) as f:
      abi: str = json.loads(await f.read())
    return abi

  async def load_contract(self, abi_name, address):
    address = self.web3.to_checksum_address(address)
    return self.web3.eth.contract(address=address, abi=await self.load_abi(abi_name))