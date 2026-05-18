from contracts.base import Base
from web3 import AsyncWeb3

class ERC20:
  def __init__(self, rpc: str, address: str):
    self.address = address
    self.base = Base(rpc)

    self.instance = None

  async def __load_contracts(self):
    if self.instance is None:
      self.instance = await self.base.load_contract("erc20", self.address)

  @property
  async def decimals(self) -> int:
    await self.__load_contracts()

    result = await self.instance.functions.decimals().call()
    return result
  
  @property
  async def symbol(self) -> str:
    await self.__load_contracts()

    result = await self.instance.functions.symbol().call()
    return result

  async def balance_of(self, address: str) -> int:
    await self.__load_contracts()

    result = await self.instance.functions.balanceOf(self.base.web3.to_checksum_address(address)).call()
    return result

  @property
  async def total_supply(self) -> int:
    await self.__load_contracts()

    return await self.instance.functions.totalSupply().call()
  
  async def transfers(self, tx_hash: str, to: str) -> list[int]:
    await self.__load_contracts()

    transfers = []
    receipt = await self.base.web3.eth.get_transaction_receipt(tx_hash)
    for log in receipt["logs"]:
      try:
        transfer = self.instance.events.Transfer().process_log(log)
      except:
        continue
      
      if AsyncWeb3.to_checksum_address(transfer['address']) == AsyncWeb3.to_checksum_address(self.address) \
      and AsyncWeb3.to_checksum_address(transfer['args']['to']) == AsyncWeb3.to_checksum_address(to):
        transfers.append(transfer['args']['value'])

    return transfers