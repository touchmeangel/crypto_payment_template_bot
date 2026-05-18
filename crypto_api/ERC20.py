from bip_utils import Bip44Changes, Bip44Coins, Bip44, Bip39SeedGenerator, Bip84, Bip84Coins, Bip39MnemonicGenerator, \
    Bip39WordsNum
from crypto_api.CryptoAsset import CryptoAsset
from dexscreener import get_token_price
from utils.retry import retry_on_429
from contracts.erc20 import ERC20 as ContractERC20
import asyncio

class ERC20(CryptoAsset):
  def __init__(self, rpc: str, symbol: str, contract: str, link: str, network: str):
    self.contract = ContractERC20(rpc, contract)
    self.__symbol = symbol
    self.__link = link
    self.__network = network

  @property
  async def symbol(self) -> str:
    return self.__symbol
  
  @property
  async def network(self) -> str:
    return self.__network
  
  @property
  async def link(self) -> str:
    return self.__link

  async def create_wallet(self, i: int = 0) -> tuple[str, str]:
    mnemonic_gen = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    mnemonic_str = mnemonic_gen.ToStr()
    seed_bytes = Bip39SeedGenerator(mnemonic_str).Generate()

    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(i).PublicKey().ToAddress()
    return mnemonic_str, bip44_addr_ctx
  
  async def price_usd(self) -> float:
    return await get_token_price(self.contract.address)
  
  @retry_on_429()
  async def get_balance(self, address: str) -> float:
    balance, decimals = await asyncio.gather(self.contract.balance_of(address), self.contract.decimals)
    return balance / 10**decimals