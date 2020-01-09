import asyncio
import os.path

import aiohttp
from PIL import Image


async def download_async(url, filepath):
    async with aiohttp.ClientSession() as session:
        async with session.get(url,) as response:
            code = response.status
            if code != 200:
                if code == 404:
                    return
                raise IOError(f"unexpected code: {code} from {url}")
            res = await response.read()
    with open(filepath, "wb") as f:
        f.write(res)


async def download_pics_async(pic_list: list, download_path: str):
    pic_url = "https://redive.estertion.win/icon/unit/{}.webp"
    pic_path = os.path.join(download_path, "{}.webp")
    tasks = [download_async(
        pic_url.format(pic_id),
        pic_path.format(pic_id)
    ) for pic_id in pic_list]
    await asyncio.gather(*tasks)


def download_pics(*args, **kwargs):
    asyncio.run(download_pics_async(*args, **kwargs))


def char_pic(id, equip=False, star=None):
    i = Image.open()
    return Image()#TODO

def teams_pic(teams):
    width = 128*5
    height = 128*len(teams)
    pic = Image.new("RGB", (width, height), 0)
    for team in teams:
        for chara in team["atk"]:
            pic.paste(char_pic(**chara))
            #TODO
