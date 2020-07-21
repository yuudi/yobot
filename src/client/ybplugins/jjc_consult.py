import asyncio
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp

from .templating import render_template
from .yobot_exceptions import ServerError


@dataclass
class Chara:
    char_id: int
    stars: Optional[int]
    equip: bool


@dataclass
class Solution:
    team: List[Chara]
    good: int
    bad: int
    time: str


class Consult:
    Passive = True
    Active = False
    Request = False
    Nicknames_csv = "https://gitee.com/yobot/pcr-nickname/raw/master/nicknames.csv"
    Nicknames_repo = "https://gitee.com/yobot/pcr-nickname/blob/master/nicknames.csv"

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.nickname_dict: Dict[str, Tuple[str, str]] = {}
        nickfile = os.path.join(glo_setting["dirname"], "nickname3.csv")
        if not os.path.exists(nickfile):
            asyncio.ensure_future(self.update_nicknames(),
                                  loop=asyncio.get_event_loop())
        else:
            with open(nickfile, encoding="utf-8-sig") as f:
                csv = f.read()
                for line in csv.split("\n")[1:]:
                    row = line.split(",")
                    for col in row:
                        self.nickname_dict[col] = (row[0], row[1])
        self.output_foler = os.path.join(self.setting['dirname'], 'output')
        self.output_num = len(os.listdir(self.output_foler))

    async def update_nicknames(self):
        nickfile = os.path.join(self.setting["dirname"], "nickname3.csv")
        try:
            async with aiohttp.request('GET', self.Nicknames_csv) as resp:
                if resp.status != 200:
                    raise ServerError(
                        "bad server response. code: "+str(resp.status))
                restxt = await resp.text()
                with open(nickfile, "w", encoding="utf-8-sig") as f:
                    f.write(restxt)
        except aiohttp.ClientError as e:
            raise RuntimeError('错误'+str(e))
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split("\n")[1:]:
                row = line.split(",")
                for col in row:
                    self.nickname_dict[col] = (row[0], row[1])

    def user_input(self, cmd: str, is_retry=False):
        def_set = set()
        in_list = cmd.split()
        if len(in_list) == 1:
            raise ValueError("请将5个名称以空格分隔")
        if len(in_list) > 5:
            raise ValueError("防守人数过多")
        for index in in_list:
            item = self.nickname_dict.get(index.lower(), None)
            if item is None:
                if is_retry:
                    msg = "没有找到【{}】，目前昵称表：{}".format(
                        index, self.Nicknames_repo)
                    asyncio.ensure_future(self.update_nicknames())
                    raise ValueError(msg)
                else:
                    self.__init__(self.setting, refresh_nickfile=True)
                    return self.user_input(cmd, True)
            def_set.add(item)
            def_lst = list(def_set)
        if len(def_lst) < 3:
            raise ValueError("防守人数过少")
        return def_lst

    async def jjcsearch_async(self, def_lst, region):
        search_source = self.setting["jjc_search"]
        try:
            if search_source == "nomae.net":
                result = await self.search_nomae_async(def_lst, region)
            elif search_source == "pcrdfans.com":
                result = await self.search_pcrdfans_async(def_lst, region)
            else:
                return f"错误的配置项：{search_source}"
        except (RuntimeError, ValueError) as e:
            return str(e)

        if len(result) == 0:
            return '没有找到公开的解法'

        page = await render_template(
            'jjc-solution.html',
            def_lst=def_lst,
            region=region,
            result=result,
            public_base=self.setting["public_basepath"],
            search_source=search_source,
        )

        self.output_num += 1
        filename = 'solution-{}-{}.html'.format(self.output_num, random.randint(0, 999))
        with open(os.path.join(self.output_foler, filename), 'w', encoding='utf-8') as f:
            f.write(page)
        addr = urljoin(
            self.setting['public_address'],
            '{}output/{}'.format(
                self.setting['public_basepath'], filename))
        reply = '找到{}条解法：{}'.format(len(result), addr)
        if self.setting['web_mode_hint']:
            reply += '\n\n如果无法打开，请仔细阅读教程中《链接无法打开》的说明'
        return reply

    def _parse_nomae_team(self, team) -> Solution:
        if team['equip'] is None:
            equip = [0]*5
        else:
            equip = team['equip'].split('_')[0].split('/')
        atk = team['atk'].split('/')[1:]
        chara_team = [Chara(
            char_id=int(self.nickname_dict[atk[i].split(',')[0]][0]),
            stars=int(atk[i].split(',')[1]),
            equip=bool(int(equip[i])),
        ) for i in range(5)]
        solution = Solution(
            team=chara_team,
            good=team['good'],
            bad=team['bad'],
            time=team['updated'],
        )
        return solution

    async def search_nomae_async(self, def_lst: list, region: int) -> List[Solution]:
        if region == 2 or region == 3:
            raise RuntimeError('当前搜索模式下无法执行此类查询')
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/78.0.3904.87 Safari/537.36'),
            'X-From': 'https://nomae.net/arenadb/',
            'Authority': 'nomae.net',
        }
        req = aiohttp.FormData()
        req.add_field('type', 'search')
        req.add_field('userid', 0)
        req.add_field('public', 1)
        for _, jpname in def_lst:
            req.add_field('def[]', jpname)
        req.add_field('page', 0)
        req.add_field('sort', 0)
        retry = 2
        while retry >= 0:
            retry -= 1
            try:
                async with aiohttp.request(
                    'POST',
                    'https://nomae.net/princess_connect/public/_arenadb/receive.php',
                    headers=headers,
                        data=req) as resp:
                    restxt = await resp.text()
            except aiohttp.ClientError as e:
                raise RuntimeError('错误'+str(e))
            try:
                receive = json.loads(restxt)
            except json.JSONDecodeError:
                continue
            return list(map(self._parse_nomae_team, receive))
        raise RuntimeError('服务器错误，请稍后再试')

    def _parse_pcrdfans_team(self, result) -> Solution:
        chara_team = [Chara(
            char_id=c['id']//100,
            stars=c['star'],
            equip=c['equip'],
        ) for c in result['atk']]
        solution = Solution(
            team=chara_team,
            good=result['up'],
            bad=result['down'],
            time=result['updated'].split('T')[0],
        )
        return solution

    async def search_pcrdfans_async(self, def_lst: list, region: int) -> List[Solution]:
        authorization = self.setting['jjc_auth_key']
        if not authorization:
            raise RuntimeError('未授权，无法查询')
        id_list = [int(char_id) * 100 + 1 for (char_id, _) in def_lst]
        headers = {
            'user-agent': 'yobot',
            'authorization': authorization,
        }
        payload = {"_sign": "a", "def": id_list, "nonce": "a",
                   "page": 1, "sort": 1, "ts": int(time.time()), "region": region}
        try:
            async with aiohttp.request(
                'POST',
                'https://api.pcrdfans.com/x/v1/search',
                headers=headers,
                json=payload,
            ) as resp:
                restxt = await resp.text()
        except aiohttp.ClientError as e:
            raise RuntimeError('错误'+str(e))
        try:
            search = json.loads(restxt)
        except json.JSONDecodeError:
            raise RuntimeError('服务器错误，请稍后再试')
        if search['code']:
            raise RuntimeError(f'查询请求被拒绝，返回值{search["code"]}')
        result = search['data']['result']
        return list(map(self._parse_pcrdfans_team, result))

    @staticmethod
    def match(cmd: str) -> int:
        if not cmd.startswith("jjc"):
            return 0
        if cmd == "jjc查询":
            return 5
        elif cmd.startswith("jjc查询"):
            return 1
        elif cmd.startswith("jjc国服"):
            return 2
        elif cmd.startswith("jjc台服"):
            return 3
        elif cmd.startswith("jjc日服"):
            return 4
        else:
            return 0

    def execute(*args, **kwargs):
        raise RuntimeError('no more sync calling supported')

    async def execute_async(self, match_num: int, msg: dict) -> dict:
        if self.setting["jjc_search"] == "off":
            return None
        elif match_num == 5:
            reply = "请接5个昵称，空格分隔"
        else:
            try:
                anlz = self.user_input(msg["raw_message"][5:])
            except ValueError as e:
                return str(e)
            reply = await self.jjcsearch_async(anlz, match_num)
        return {
            "reply": reply,
            "block": True
        }
