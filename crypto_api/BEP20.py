from crypto_api.ERC20 import ERC20
from config import BSC_RPC

class BEP20(ERC20):
  def __init__(self, symbol: str, contract: str):
    super().__init__(BSC_RPC, symbol, contract, f"https://bscscan.com/token/{contract}", "BSC")