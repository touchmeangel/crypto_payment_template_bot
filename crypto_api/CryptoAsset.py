from abc import ABC, abstractmethod

class CryptoAsset(ABC):
  @property
  @abstractmethod
  async def symbol(self) -> str:
    pass
  
  @property
  @abstractmethod
  async def network(self) -> str:
    pass

  @property
  @abstractmethod
  async def link(self) -> str:
    pass
  
  @abstractmethod
  async def create_wallet(self, i: int = 0) -> tuple[str, str]:
    pass

  @abstractmethod
  async def price_usd(self) -> float:
    pass

  @abstractmethod
  async def get_balance(self, address: str) -> float:
    pass