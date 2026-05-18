from utils.retry import retry_on_429
import aiohttp

@retry_on_429()
async def get_token_price(token_address):
  async with aiohttp.ClientSession() as session:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    async with session.get(url) as response:
      data = await response.json()
      pairs = data.get("pairs")
      return float(pairs[0]["priceUsd"]) if pairs else 0.0