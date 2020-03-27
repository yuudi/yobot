import aiohttp
import requests

_shorten_api = 'http://go.yobot.monster/yourls-api.php'
_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
}


def shorten(url: str) -> str:
    data = {
        'signature': '52cd522abf',
        'action': 'shorturl',
        'url': url,
        'format': 'simple'
    }
    try:
        resp = requests.post(_shorten_api, data=data, headers=_header)
    except requests.exceptions.ConnectionError:
        pass
    else:
        if resp.status_code == 200:
            url = resp.text
    return url


async def shorten_async(url: str) -> str:
    data = {
        'signature': '52cd522abf',
        'action': 'shorturl',
        'url': url,
        'format': 'simple'
    }
    try:
        async with aiohttp.request('POST', url=_shorten_api, data=data, headers=_header) as response:
            if response.status == 200:
                url = await response.text()
    except aiohttp.ClientError:
        pass
    return url
