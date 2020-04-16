import json
import os
import random
from urllib.parse import urljoin

import aiohttp
import requests

from .templating import render_template
from .yobot_exceptions import ServerError


def _parse_team(team):
    if team['equip'] is None:
        equip = [0]*5
    else:
        equip = team['equip'].split('_')[0].split('/')
    atk = team['atk'].split('/')[1:]
    return [[
        atk[i].split(',')[0],
        int(atk[i].split(',')[1]),
        bool(int(equip[i])),
    ] for i in range(5)]


class Consult:
    Passive = True
    Active = False
    Request = False
    URL = "http://api.yobot.xyz/v3/nickname/old.csv"
    Feedback_URL = "http://api.yobot.xyz/v2/nicknames/?type=feedback&name="
    Nicknames_repo = "https://gitee.com/yobot/pcr-nickname/blob/master/nicknames.csv"

    def __init__(self, glo_setting: dict, *args, refresh_nickfile=False,  **kwargs):
        self.setting = glo_setting
        self.name2jp = {}
        self.jpname2id = {}
        self.search_URL = glo_setting["jjc_search_url"]
        nickfile = os.path.join(glo_setting["dirname"], "nickname.csv")
        if refresh_nickfile or not os.path.exists(nickfile):
            res = requests.get(self.URL)
            if res.status_code != 200:
                raise ServerError(
                    "bad server response. code: "+str(res.status_code))
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split():
                row = line.split(",")
                for col in row[1:]:
                    self.name2jp[col] = row[2]
                self.jpname2id[row[2]] = int(row[0])

    def user_input(self, cmd: str, is_retry=False):
        def_set = set()
        in_list = cmd.split()
        if len(in_list) == 1:
            raise ValueError("请将5个名称以空格分隔")
        if len(in_list) > 5:
            raise ValueError("防守人数过多")
        for index in in_list:
            item = self.name2jp.get(index.lower(), None)
            if item is None:
                if is_retry:
                    try:
                        requests.get(self.Feedback_URL+index)
                    except requests.exceptions.ConnectionError:
                        msg = "没有找到【{}】，目前昵称表：{}".format(
                            index, self.Nicknames_repo)
                    else:
                        msg = "没有找到【{}】，已自动反馈，目前昵称表：{}".format(
                            index, self.Nicknames_repo)
                    raise ValueError(msg)
                else:
                    self.__init__(self.setting, refresh_nickfile=True)
                    return self.user_input(cmd, True)
            def_set.add(item)
            def_lst = list(def_set)
        if len(def_lst) < 3:
            raise ValueError("防守人数过少")
        return def_lst

    async def jjcsearch_async(self, def_lst: list, retry: int = 0) -> str:
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
        for item in def_lst:
            req.add_field('def[]', item)
        req.add_field('page', 0)
        req.add_field('sort', 0)
        try:
            async with aiohttp.request(
                'POST',
                'https://nomae.net/princess_connect/public/_arenadb/receive.php',
                headers=headers,
                    data=req) as resp:
                restxt = await resp.text()
        except aiohttp.ClientError as e:
            return '错误'+str(e)
        try:
            solution = json.loads(restxt)
        except json.JSONDecodeError as e:
            if retry >= 2:
                return '服务器错误，请稍后再试'
            else:
                return await self.jjcsearch_async(def_lst, retry+1)
        if len(solution) == 0:
            return '没有找到公开的解法'

        page = await render_template(
            'jjc-solution.html',
            len=len,
            solution=solution,
            def_lst=def_lst,
            jpname2id=self.jpname2id,
            parse_team=_parse_team,
            public_base=self.setting["public_basepath"],
        )

        output_foler = os.path.join(self.setting['dirname'], 'output')
        num = len(os.listdir(output_foler)) + 1
        os.mkdir(os.path.join(output_foler, str(num)))
        filename = 'solution-{}.html'.format(random.randint(0, 999))
        with open(os.path.join(output_foler, str(num), filename), 'w', encoding='utf-8') as f:
            f.write(page)
        addr = urljoin(
            self.setting['public_address'],
            '{}output/{}/{}'.format(
                self.setting['public_basepath'], num, filename))
        reply = '找到{}条解法：{}'.format(len(solution), addr)
        if self.setting['web_mode_hint']:
            reply += '\n\n如果连接无法打开，请参考https://gitee.com/yobot/yobot/blob/master/documents/usage/cannot-open-webpage.md'
        return reply

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "jjc查询":
            return 1
        elif cmd.startswith("jjc查询"):
            return 2
        else:
            return 0

    def execute(*args, **kwargs):
        raise RuntimeError('no more sync calling supported')

    async def execute_async(self, match_num: int, msg: dict) -> dict:
        if self.setting.get("jjc_consult", True) == False:
            return None
        elif match_num == 1:
            reply = "请接5个昵称，空格分隔"
        else:
            try:
                anlz = self.user_input(msg["raw_message"][5:])
            except ValueError as e:
                return str(e)
            reply = await self.jjcsearch_async(anlz)
        return {
            "reply": reply,
            "block": True
        }
