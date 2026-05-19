import os
import aiohttp

def start_ngrok():
  from pyngrok import ngrok
  ngrok_token = os.environ.get("NGROK_TOKEN")
  port = os.environ.get("WEBAPP_PORT")
  ngrok.set_auth_token(ngrok_token)
  http_tunnel = ngrok.connect(f":{port}", "http")
  return http_tunnel.public_url

async def get_ngrok_public_url(ngrok_hostname: str):
  async with aiohttp.ClientSession() as session:
    async with session.get(f"http://{ngrok_hostname}/api/tunnels", timeout=5) as resp:
      resp.raise_for_status()
      data = await resp.json()
      for t in data.get("tunnels", []):
        pub = t.get("public_url", "")
        if pub.startswith("https://"):
          return pub

async def get_webhook_host(ngrok_hostname: str | None = None) -> str:
  if ngrok_hostname is None:
    host = start_ngrok()
    if host is None:
      raise RuntimeError(f"Local ngrock returned no public url")
    return host

  public = await get_ngrok_public_url(ngrok_hostname)  
  if public is None:
    raise RuntimeError(f"Could not fetch ngrok public URL from http://{ngrok_hostname}")
  
  return public