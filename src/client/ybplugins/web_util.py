import os
import random
import string
from urllib.parse import urljoin

import aiohttp
import peewee as pw
import requests
from quart import Quart, jsonify, request, send_file, session

from .yobot_exceptions import ServerError

_rand_string_chaset = (string.ascii_uppercase +
                       string.ascii_lowercase +
                       string.digits)


def rand_string(n=16):
    return ''.join(
        random.choice(_rand_string_chaset)
        for _ in range(n)
    )


def async_cached_func(maxsize=64):
    cache = {}

    def decorator(fn):
        async def wrapper(*args, nocache=False):  # args must be hashable
            key = tuple(args)
            if nocache or (key not in cache):
                if len(cache) >= maxsize:
                    del cache[cache.keys().next()]
                cache[key] = await fn(*args)
            return cache[key]
        return wrapper
    return decorator


ip_cache = pw.SqliteDatabase(None)


class IP_Location(pw.Model):
    ip = pw.IPField(primary_key=True)
    location = pw.TextField()

    class Meta:
        database = ip_cache


@async_cached_func(128)
async def _ip_location(ip: str) -> str:
    cache = IP_Location.get_or_none(ip=ip)
    if cache is not None:
        return cache.location
    async with aiohttp.request("GET", url=f'http://freeapi.ipip.net/{ip}') as response:
        if response.status != 200:
            raise ServerError(f'http code {response.status} from ipip.net')
        res = await response.json()
    location = ''.join(res)
    IP_Location.create(
        ip=ip,
        location=location,
    )
    return location


class WebUtil:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 *args, **kwargs):
        self.setting = glo_setting
        self.resource_path = os.path.join(
            glo_setting['dirname'], 'output', 'resource')
        if not os.path.exists(self.resource_path):
            os.makedirs(self.resource_path)

        ip_cache.init(
            database=os.path.join(
                glo_setting['dirname'], 'ip_location_cache.db'),
            pragmas={
                'journal_mode': 'wal',
                'cache_size': -1024,
            },
        )
        if not IP_Location.table_exists():
            IP_Location.create_table()

        if not os.path.exists(os.path.join(self.resource_path, 'background.jpg')):
            try:
                r = requests.get(
                    'https://i.loli.net/2020/05/31/IirkP9TpnV7Ks6q.jpg')
                assert r.status_code == 200
                with open(os.path.join(self.resource_path, 'background.jpg'), 'wb') as f:
                    f.write(r.content)
            except Exception as e:
                print(e)

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
            except Exception as e:
                print(e)
                location = 'unknown'
            return jsonify([location])

        @app.route(
            urljoin(self.setting['public_basepath'], 'api/get-domain/'),
            methods=['GET'])
        async def yobot_api_getdomain():
            if 'yobot_user' not in session:
                return jsonify(code=400, message='Unauthorized')
            name = request.args.get('name')
            if name is None:
                return jsonify(code=400, message='No name specified')
            try:
                async with aiohttp.request('GET', url='http://api2.yobot.win/getdomain/?name='+name) as response:
                    if response.status != 200:
                        raise ServerError(
                            f'http code {response.status} from api2.yobot.win')
                    res = await response.json()
            except:
                return jsonify(code=401, message='Fail: Connect to Server')
            return jsonify(res)

        @app.route(
            urljoin(self.setting["public_basepath"],
                    "resource/<path:filename>"),
            methods=["GET"])
        async def yobot_resource(filename):
            localfile = os.path.join(self.resource_path, filename)
            if not os.path.exists(localfile):
                if filename.endswith('.jpg'):
                    filename = filename[:-4] + '.webp@w400'
                try:
                    async with aiohttp.request(
                        "GET",
                        url=f'https://redive.estertion.win/{filename}'
                    ) as response:
                        res = await response.read()
                        if response.status != 200:
                            return res, response.status
                except aiohttp.ClientError as e:
                    print(e)
                    return '404: Not Found', 404
                if not os.path.exists(os.path.dirname(localfile)):
                    os.makedirs(os.path.dirname(localfile))
                with open(localfile, 'wb') as f:
                    f.write(res)
            return await send_file(localfile)
