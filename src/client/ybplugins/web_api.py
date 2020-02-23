from urllib.parse import urljoin

import aiohttp
from quart import Quart, jsonify, request, session

from .yobot_exceptions import ServerError


def async_cached_func(maxsize=64):
    cache = {}

    def decorator(fn):
        async def wrapper(*args):  # args must be hashable
            key = tuple(args)
            if key not in cache:
                if len(cache) >= maxsize:
                    del cache[cache.keys().next()]
                cache[key] = await fn(*args)
            return cache[key]
        return wrapper
    return decorator


@async_cached_func(32)
async def _ip_location(ip):
    async with aiohttp.request("GET", url=f'http://freeapi.ipip.net/{ip}') as response:
        if response.status != 200:
            raise ServerError(f'http code {response.status} from ipip.net')
        res = await response.json()
    return res


class WebApi:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 *args, **kwargs):
        self.setting = glo_setting

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'api/ip-location/'),
            methods=['GET'])
        async def yobot_api_iplocation():
            if 'yobot_user' not in session:
                return jsonify(['unauthorized'])
            ip = request.args.get('ip')
            if ip is None:
                return jsonify(['unknown'])
            try:
                location = await _ip_location(ip)
            except:
                location = ['unknown']
            return jsonify(location)
