from bip_utils import Bip44Changes, Bip44Coins, Bip44, Bip39SeedGenerator, Bip84, Bip84Coins, Bip39MnemonicGenerator, \
    Bip39WordsNum
from crypto_api.CryptoAsset import CryptoAsset
from utils.retry import retry_on_429
import aiohttp

@retry_on_429()
async def get_tron_token_price(token_address):
  async with aiohttp.ClientSession() as session:
    url = f"https://apilist.tronscanapi.com/api/token_trc20?contract={token_address}"
    async with session.get(url) as response:
      data = await response.json()
      tokens = data.get("trc20_tokens")
      if not tokens:
        return 0.0
      try:
        token = tokens[0]
      except IndexError:
        return 0.0
      market_info = token.get("market_info")
      if not market_info:
        return 0.0
      price_in_usd = market_info.get("priceInUsd")
      return float(price_in_usd) if price_in_usd else 0.0

class TRC20(CryptoAsset):
  def __init__(self, symbol: str, contract: str):
    self.contract = contract
    self.__symbol = symbol
    self.__link = f"https://tronscan.org/#/token20/{self.contract}"

  @property
  async def symbol(self) -> str:
    return self.__symbol
  
  @property
  async def network(self) -> str:
    return "TRON"
  
  @property
  async def link(self) -> str:
    return self.__link

  async def create_wallet(self, i: int = 0) -> tuple[str, str]:
    mnemonic_gen = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    mnemonic_str = mnemonic_gen.ToStr()
    seed_bytes = Bip39SeedGenerator(mnemonic_str).Generate()

    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(i).PublicKey().ToAddress()
    return mnemonic_str, bip44_addr_ctx
  
  async def price_usd(self) -> float:
    return await get_tron_token_price(self.contract)
  
  @retry_on_429()
  async def get_balance(self, address: str) -> float:
    url = f"https://apilist.tronscan.org/api/account?address={address}&includeToken=true"
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        data = await response.json()

        token_balance = None
        for token in data['trc20token_balances']:
            if token['tokenId'] == self.contract:
                token_balance = round(float(token['balance']) * pow(10, -token['tokenDecimal']), 6)
                break
        
        if token_balance is not None:
            return token_balance
        else:
            return 0.0