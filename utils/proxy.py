
from urllib.parse import urlparse

def parse_proxy_url(proxy_url: str):
    # Parse the proxy URL
    parsed = urlparse(proxy_url)

    # Extract components
    proxy = {
        "scheme": parsed.scheme,  # e.g., 'socks5', 'http'
        "hostname": parsed.hostname,
        "port": parsed.port,
        "username": parsed.username,
        "password": parsed.password
    }

    return proxy