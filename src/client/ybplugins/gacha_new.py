import asyncio
from typing import Any, Dict, Union, List, Tuple, NamedTuple

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart, session, request, redirect, url_for
from .templating import render_template
from .ybdata import User
from urllib.parse import urljoin

import random
import pickle
import os
import sqlite3
import json
import re
import time

STAR_HIISHI = [1, 10, 50]
STAR_STR = "★"
STAR_EMOJI_STR = "⭐"


# 抽卡结果项
class GachaItem(NamedTuple):
    name: str   # 角色名称
    star: int   # 角色星级
    up: bool    # 是否为卡池 UP

    def to_str(self, new: bool) -> str:
        """将抽卡结果项格式化为字符串

        Args:
            new (bool): 是否为 New 的角色

        Returns:
            str: 格式化后的字符串
        """
        return "{0:{1}<8}（{2}）".format(STAR_STR * self.star + self.name + ("↑" if self.up else ""), "　", (f"🔮×{STAR_HIISHI[self.star - 1]}" if not new else "NEW!"))


# 抽卡结果统计类
class GachaInfo:
    def __init__(self, pool):
        """初始化抽卡结果

        Args:
            pool (GachaPool): 抽卡的池子
        """
        self.gacha_count: int = 0                   # 抽卡次数
        self.star_count: List[int] = [0, 0, 0]      # 1、2、3星角色数量
        self.new_count: List[int] = [0, 0, 0]       # 1、2、3星角色 new 数量
        self.up_count: int = 0                      # 获得卡池 UP 角色的数量
        self.first_up: int = 0                      # 首次获得 UP 角色的抽取数
        self.add_hiishi: int = 0                    # 增加的女神的秘石数量
        self.pool: GachaPool                        # 所抽的卡池

    def append(self, item: GachaItem, new: bool):
        """接受抽卡结果项以建立统计数据

        Args:
            item (GachaItem): 抽卡的结果项
            new (bool): 该抽卡结果对应的角色是否为 new
        """
        self.gacha_count += 1
        self.star_count[item.star - 1] += 1
        self.new_count[item.star - 1] += (1 if new else 0)
        self.up_count += (1 if item.up else 0)
        if self.first_up == 0 and item.up:
            self.first_up = self.gacha_count
        self.add_hiishi += STAR_HIISHI[item.star - 1]


# 子奖池相关的信息
class GachaSubPoolItem(NamedTuple):
    name: str = ""              # 子奖池名
    star: int = 1               # 子奖池对应星级
    prob: int = 0               # 非保底抽的相对概率
    last_prob: int = 0          # 保底抽的相对概率
    is_up: bool = False         # 是否为 UP 子奖池
    charas: List[str] = []      # 包含的角色名称列表


# 卡池类
class GachaPool:
    def __init__(self, gacha_pool: dict):
        """初始化一个抽奖卡池

        Args:
            gacha_pool (dict): 从配置文件中读取到的卡池信息
        """
        self.name = gacha_pool.get("name", "")              # 卡池名
        self.describe = gacha_pool.get("describe", None)    # 卡池简介
        self.regex = gacha_pool.get("regex", self.name)     # 匹配该卡池的正则表达式
        config_sub_pools = gacha_pool["sub_pools"]
        self.total_prob = 0                                 # 卡池的非保底抽总相对概率
        self.total_last_prob = 0                            # 卡池的保底抽总相对概率
        # 卡池包含的子奖池 List[GachaSubPoolItem]
        self.sub_pools = []
        for p in config_sub_pools:
            charas = p.get("charas", [])
            if len(charas) == 0:
                continue
            star = p.get("star", 1)
            prob = p.get("prob", 0)
            self.total_prob += prob
            last_prob = p.get("last_prob", 0)
            self.total_last_prob += last_prob
            is_up = p.get("is_up", False)
            name = p.get(
                "name", f"{star}星{len(charas)}角色{('非' if not is_up else '')}UP池")
            self.sub_pools.append(GachaSubPoolItem(
                name, star, prob, last_prob, is_up, charas))
        self.sort_prob_sub_pools = sorted(self.sub_pools, key=lambda x: x.prob)
        self.sort_last_prob_sub_pools = sorted(
            self.sub_pools, key=lambda x: x.last_prob)

    def get_pool_info(self) -> str:
        """将卡池信息整理成字符串

        Returns:
            str: 卡池信息字符串
        """
        msg = [f"卡池名：{self.name}"]
        msg.append("简介：{}".format(
            "无" if self.describe is None or self.describe == "" else self.describe))
        for idx, p in enumerate(self.sort_prob_sub_pools):
            msg.append(f"奖池 {idx + 1}：{p.name}")
            msg.append(
                f"概率：非保底抽 {round(p.prob / self.total_prob * 100, 3)}%， 保底抽 {round(p.last_prob / self.total_last_prob * 100, 3)}%")
            msg.append(
                f"属性：{STAR_EMOJI_STR * p.star} {'↑↑↑' if p.is_up else ''}")
            msg.append(f"角色：{'、'.join(p.charas)} （{len(p.charas)}）")
        return "\n".join(msg)

    def get_up_list(self) -> List[str]:
        """取得本卡池的 UP 角色名称列表

        Returns:
            List[str]: 本卡池的 UP 角色名称列表
        """
        charas = []
        for x in self.sort_prob_sub_pools:
            if x.is_up:
                for c in x.charas:
                    charas.append(c)
        return charas


# 卡池管理类
class GachaPoolsMgr:
    def __init__(self, config: dict):
        """根据配置文件初始化所有的卡池

        Args:
            config (dict): 抽卡相关的配置文件信息
        """
        self.pools = [GachaPool(x) for x in config["pools"]
                      ]                    # 包含的所有卡池 List[GachaPool]
        # 卡池的名称索引
        self.pools_names = [x.name for x in self.pools]
        # 卡池的正则表达式索引
        self.pools_regex = [x.regex for x in self.pools]
        self.default_pool_name = config["settings"].get(
            "default_pool", "")     # 默认卡池的名称
        # 默认卡池 GachaPool
        self.default_pool = self.pools[0]
        if self.default_pool_name in self.pools_names:
            self.default_pool = self.pools[self.pools_names.index(
                self.default_pool_name)]
        else:
            self.default_pool_name = self.default_pool.name

    def get_pool_by_name(self, name: str) -> Union[GachaPool, None]:
        """通过卡池名称取得具体卡池信息

        Args:
            name (str): 卡池名称

        Returns:
            Union[GachaPool, None]: 具体卡池信息，找不到则返回 None
        """
        if name in self.pools_names:
            return self.pools[self.pools_names.index(name)]
        return None

    def get_pool_by_index(self, index: int) -> Union[GachaPool, None]:
        """通过卡池序号取得具体卡池信息

        Args:
            index (int): 卡池序号

        Returns:
            Union[GachaPool, None]: 具体卡池信息，找不到则返回 None
        """
        idx = index - 1
        if idx < 0 or idx >= len(self.pools_names):
            return None
        else:
            return self.pools[idx]

    def get_pool_by_regex(self, string: str) -> Union[GachaPool, None]:
        """通过卡池正则表达式取得具体卡池信息

        Args:
            string (str): 卡池的正则表达式

        Returns:
            Union[GachaPool, None]: 具体卡池信息，找不到则返回 None
        """
        for idx, regex in enumerate(self.pools_regex):
            if regex == "":
                continue
            if re.match(regex, string) is not None:
                return self.pools[idx]
        return None

    def get_pool(self, string: str) -> Union[GachaPool, None]:
        """按正则表达式、卡池名、序号的方式匹配卡池

        Args:
            string (str): 传入的匹配字符串

        Returns:
            Union[GachaPool, None]: 具体卡池信息，找不到则返回 None
        """
        pool = self.get_pool_by_regex(string)
        if pool is not None:
            return pool
        pool = self.get_pool_by_name(string)
        if pool is not None:
            return pool
        try: 
            index = int(string)
            return self.get_pool_by_index(index)
        except ValueError:
            return None


def check_gacha_config(config: dict) -> bool:
    """检查配置文件

    Args:
        config (dict): 配置内容

    Returns:
        bool: 是否合法
    """
    try:
        settings = config["settings"]
        if not isinstance(settings.get("new_jewels_count", 80000), int):
            return False
        if not isinstance(settings.get("daily_jewels_count", 5000), int):
            return False
        if not isinstance(settings.get("default_pool", ""), str):
            return False
        pools = config["pools"]
        if (not isinstance(pools, list)) or len(pools) == 0:
            return False
        for p in pools:
            if not isinstance(p.get("name", ""), str):
                return False
            if not isinstance(p.get("describe", ""), str):
                return False
            if not isinstance(p.get("regex", ""), str):
                return False
            sub_pools = p.get("sub_pools", [])
            if not isinstance(sub_pools, list) or len(sub_pools) == 0:
                return False
            for sp in sub_pools:
                if not isinstance(sp.get("name", ""), str):
                    return False
                if not isinstance(sp.get("prob", 0), int):
                    return False
                if not isinstance(sp.get("last_prob", 0), int):
                    return False
                star = sp.get("star", 1)
                if not isinstance(star, int):
                    return False
                elif star not in [1, 2, 3]:
                    return False
                if not isinstance(sp.get("is_up", False), bool):
                    return False
                charas = sp.get("charas", [])
                if not isinstance(charas, list) or len(charas) == 0:
                    return False
        return True
    except:
        return False


# 抽卡指令处理类
class GachaNew:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.api = bot_api

        self.active = True
        if not self.setting.get("gacha_new_on", False):
           self.active = False

        self.gacha_config_path = os.path.join(
            self.setting["dirname"], "gacha_new_config.json")
        with open(self.gacha_config_path, "r", encoding="utf-8") as f:
            try:
                self.config = json.load(f)
                if not check_gacha_config(self.config):
                   self.active = False
                   print("新版抽卡配置文件校验不通过，已禁用新版抽卡功能")
                   return
            except json.JSONDecodeError:
                self.active = False
                print("新版抽卡配置文件含有语法错误，已禁用新版抽卡功能")
                return

        self.gacha_mgr = GachaPoolsMgr(self.config)

        self.new_jewels_count = self.config["settings"].get(
            "new_jewels_count", 80000)
        self.daily_jewels_count = self.config["settings"].get(
            "daily_jewels_count", 5000)
        self.admin_list = self.config["settings"].get("extra_gacha_admin_qqid", []) + \
            self.setting["super-admin"]

        db_exists = os.path.exists(os.path.join(
            self.setting["dirname"], "gacha.db"))
        self.db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "gacha.db"))
        db = self.db_conn.cursor()
        if not db_exists:
            db.execute('''CREATE TABLE Colle(
                            qqid INT PRIMARY KEY,
                            colle BLOB,
                            hiishi INTEGER,
                            remain_jewel INTEGER,
                            used_jewel INTEGER,
                            last_reincarnated_time INTEGER,
                            reincarnated_count INTEGER
                        )''')
            db.execute("CREATE TABLE System(last_jewel_time INTEGER)")
            db.execute("INSERT INTO System(last_jewel_time) VALUES(?)",
                       (int(time.time()),))
            self.db_conn.commit()
        else:
            sql_info = list(db.execute("SELECT last_jewel_time FROM System"))
            last_jewel_time = time.localtime(sql_info[0][0])
            now = time.localtime(time.time())
            need_jewel = False
            if last_jewel_time.tm_mday < now.tm_mday:
                need_jewel = True
            elif last_jewel_time.tm_mday == now.tm_mday and \
                    now.tm_hour >= 5 and last_jewel_time.tm_hour < 5:
                need_jewel = True
            if need_jewel:
                db.execute(
                    "UPDATE Colle SET remain_jewel = remain_jewel + {}".format(self.daily_jewels_count))
                db.execute("UPDATE System SET last_jewel_time = {}".format(
                    int(time.time())))
                self.db_conn.commit()
        db.close()

        @scheduler.scheduled_job('cron', hour=5)
        async def daily_add_jewel():
            db = self.db_conn.cursor()
            db.execute(
                "UPDATE Colle SET remain_jewel = remain_jewel + {}".format(self.daily_jewels_count))
            db.execute("UPDATE System SET last_jewel_time = {}".format(
                int(time.time())))
            self.db_conn.commit()
            db.close()
        
        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/gacha_new/config.html'),
                methods=['GET'])
        async def gacha_new_config_html():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            return await render_template(
                'admin/gacha-new-config.html',
                user=User.get_by_id(session['yobot_user']),
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/gacha_new/config.json'),
                methods=['GET', 'POST'])
        async def gacha_new_config_json():
            if 'yobot_user' not in session:
                return "未登录", 401
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group != 1:
                return "无权访问", 403
            if request.method == "GET":
                with open(self.gacha_config_path, "r", encoding="utf-8") as f:
                    return f.read(), 200, {"content-type": "application/json"}
            elif request.method == "POST":
                new_config = await request.get_json()
                req_csrf_token = request.headers.get("X-CSRF-TOKEN")
                if req_csrf_token != session["csrf_token"]:
                    return "Invalid CSRF Token", 403
                if not check_gacha_config(new_config):
                    return "配置文件校验不通过", 400
                config_string = json.dumps(new_config, ensure_ascii=False, indent=4)
                with open(self.gacha_config_path, "w", encoding="utf-8") as f:
                    f.write(config_string)
                self.config = new_config
                self.gacha_mgr = GachaPoolsMgr(self.config)
                self.new_jewels_count = self.config["settings"].get(
                    "new_jewels_count", 80000)
                self.daily_jewels_count = self.config["settings"].get(
                    "daily_jewels_count", 5000)
                self.admin_list = self.config["settings"].get("extra_gacha_admin_qqid", []) + \
                    self.setting["super-admin"]
                return "成功", 200

    def gacha_one(self, gacha_pool: GachaPool, last: bool = False) -> GachaItem:
        """单抽

        Args:
            gacha_pool (GachaPool): 抽卡的卡池
            last (bool, optional): 是否为保底抽，默认为否

        Returns:
            GachaItem: 抽卡结果项
        """
        prob = (gacha_pool.total_prob if not last else gacha_pool.total_last_prob)
        rand = random.randint(1, prob)
        sub_pools = []
        if not last:
            sub_pools = gacha_pool.sort_prob_sub_pools
        else:
            sub_pools = gacha_pool.sort_last_prob_sub_pools
        summ = 0
        for p in sub_pools:
            summ += (p.prob if not last else p.last_prob)
            if rand <= summ:
                return GachaItem(random.choice(p.charas), p.star, p.is_up)

    def gacha_ten(self, gacha_pool: GachaPool) -> List[GachaItem]:
        """十连

        Args:
            gacha_pool (GachaPool): 抽卡的卡池

        Returns:
            List[GachaItem]: 抽卡结果项列表
        """
        get_list = []
        for _ in range(9):
            get_list.append(self.gacha_one(gacha_pool, False))
        get_list.append(self.gacha_one(gacha_pool, True))
        return get_list

    def gacha_300(self, gacha_pool: GachaPool) -> List[GachaItem]:
        """抽一井

        Args:
            gacha_pool (GachaPool): 抽卡的卡池

        Returns:
            List[GachaItem]: 抽卡结果项列表
        """
        get_list = []
        for _ in range(30):
            temp = self.gacha_ten(gacha_pool)
            for x in temp:
                get_list.append(x)
        return get_list

    def comment_res(self, info: GachaInfo) -> List[str]:
        """对抽卡结果进行评价
        特别感谢 BrotherPPot (https://github.com/BrotherPPot) 提供建议和文案

        Args:
            info (GachaInfo): 抽卡结果统计信息

        Returns:
            List[str]: 评价语句列表
        """
        msg = []
        if info.gacha_count == 1:
            if info.up_count == 1:
                msg.append("wdnmd，真就一发入魂呗")
            elif info.star_count[2] == 1:
                msg.append("众所周知，单抽出奇迹")
            elif info.star_count[1] == 1:
                msg.append("还行，10个母猪石")
            elif info.star_count[0] == 1:
                msg.append("母猪石+1")
        if info.gacha_count == 10:
            msg.append(f"本次十连新增女神的秘石×{info.add_hiishi}。")
            if info.star_count[2] >= 3:
                msg.append("有这种运气，为什么不去买彩票呢？")
            elif info.star_count[2] == 2:
                msg.append("嗯哼？快乐的双黄蛋？")
            elif info.star_count[2] == 1:
                msg.append("めでたし，可喜可贺")
            elif info.up_count == 1:
                msg.append("おめでとう，恭喜出货。")
            elif info.star_count[1] >= 5:
                msg.append("母猪石拉满，不亏")
            elif info.star_count[1] == 1 and info.star_count[0] == 9:
                msg.append("根据运气守恒定理，下一发必出彩")
            else:
                msg.append("常规操作")
        elif info.gacha_count == 300:
            msg.append(
                f"{STAR_EMOJI_STR * 3}×{info.star_count[2]} {STAR_EMOJI_STR * 2}×{info.star_count[1]} {STAR_EMOJI_STR}×{info.star_count[0]}")
            msg.append(f"🔮×{info.add_hiishi}")
            if info.up_count > 0:
                msg.append(f"第 {info.first_up} 抽首次获得 UP 角色。")
            if info.up_count == 0:
                if info.star_count[2] == 0:
                    msg.append("太惨了，咱们还是退款删游吧...")
                elif info.star_count[2] > 7:
                    up_list = info.pool.get_up_list()
                    msg.append("{0}呢？我的{0}呢？".format(
                        "up" if len(up_list) != 1 else up_list[0]))
                elif info.star_count[2] <= 3:
                    msg.append("啊，是心梗的感觉！")
                else:
                    msg.append("据说天井的概率只有12.16%")
            elif info.up_count >= 3:
                if info.star_count[2] >= 7:
                    msg.append("按F捕杀这只成熟的海豹")
                elif info.star_count[2] <= 4:
                    msg.append("从某种程度上来讲，你也是一条欧蝗了。")
                # elif first_up < 100:
                #     msg.append("已经可以了，您已经很欧了")
                # elif first_up > 290:
                #     msg.append("标 准 结 局")
                #     msg.append("有些人看上去是井了，其实是多了50母猪石。")
                # elif first_up > 250:
                #     msg.append("补井还是不补井，这是一个问题...")
                # else:
                #     msg.append("期望之内，亚洲水平")
            elif info.up_count > 0:
                if info.first_up < 50:
                    msg.append("发现海豹，建议口球处理")
                elif info.first_up < 100:
                    msg.append("哎哟不错哟，欧气满满。")
                elif info.first_up < 160:
                    msg.append("常规操作，平均水平，稳得一批")
                elif info.first_up > 250:
                    msg.append("补井还是不补井，这是个问题......")
                elif info.first_up >= 280:
                    msg.append("抽满300连，白嫖50母猪石不亏的😢😢😢😢")
                else:
                    msg.append("平凡无奇，出了就行")
            if info.add_hiishi > 1600:
                msg.append("可能只有开养猪场的才有这么多母猪石吧")
            elif (info.star_count[2] >= 7 and info.star_count[2] <= 8) or info.add_hiishi >= 1368:
                msg.append("符合期望，满足预期，您就是均值玩家。")
            elif info.add_hiishi > 1000:
                msg.append("石头有点少，但问题不大")
            else:
                msg.append("骑士大人，不要气馁，有我在哦( •̀ ω •́ )✧")
        return msg

    def gacha(self, qqid: int, gacha_name: Union[str, None], gacha_count: int) -> str:
        """抽卡主函数

        Args:
            qqid (int): 抽卡的用户 QQ 号
            gacha_name (Union[str, None]): 抽卡的卡池名称
            gacha_count (int): 抽卡次数，1、10或300

        Returns:
            str: 抽卡结果消息
        """
        db = self.db_conn.cursor()
        sql_info = list(db.execute(
            "SELECT colle, hiishi, remain_jewel, used_jewel FROM Colle WHERE qqid = ?", (qqid,)))
        mem_exists = (len(sql_info) == 1)
        colle = []
        hiishi = 0
        remain_jewel = self.new_jewels_count
        used_jewel = 0
        if mem_exists:
            colle = pickle.loads(sql_info[0][0])
            hiishi = sql_info[0][1]
            remain_jewel = sql_info[0][2]
            used_jewel = sql_info[0][3]

        if remain_jewel - 150 * gacha_count < 0:
            if not mem_exists:
                colle = pickle.dumps([])
                db.execute("INSERT INTO Colle(qqid, colle, hiishi, remain_jewel, used_jewel, last_reincarnated_time, reincarnated_count) VALUES(?, ?, 0, ?, 0, ?, 0)",
                           (qqid, colle, self.new_jewels_count, int(time.time())))
                self.db_conn.commit()
            db.close()
            return f"[CQ:at,qq={qqid}]，您的钻石不足，仅剩余💎×{remain_jewel}，请等待每日 5:00 赠送💎×{self.daily_jewels_count} 或联系卡池管理员为您充值。"

        msg = []

        if gacha_name == "":
            gacha_pool = self.gacha_mgr.default_pool
        else:
            gacha_pool = self.gacha_mgr.get_pool(gacha_name)
            if gacha_pool is None:
                msg.append(
                    f"(没有找到相应卡池，将为您抽取默认卡池：{self.gacha_mgr.default_pool_name})")
                gacha_pool = self.gacha_mgr.default_pool

        msg.append(f"[CQ:at,qq={qqid}]，素敵な仲間が増えますよ！")
        gacha_info = GachaInfo(gacha_pool)
        res = []
        if gacha_count == 300:
            res = self.gacha_300(gacha_pool)
        elif gacha_count == 10:
            res = self.gacha_ten(gacha_pool)
        elif gacha_count == 1:
            res = [self.gacha_one(gacha_pool)]
        for item in res:
            is_new = ((item.name, item.star) not in colle)
            if is_new:
                colle.append((item.name, item.star))
            if gacha_count == 300:
                if item.star == 3 or item.up:
                    msg.append(item.to_str(is_new))
            else:
                msg.append(item.to_str(is_new))
            gacha_info.append(item, is_new)
        for x in self.comment_res(gacha_info):
            msg.append(x)
        hiishi += gacha_info.add_hiishi
        remain_jewel -= gacha_count * 150
        msg.append(f"（剩余💎×{remain_jewel}）")
        used_jewel += gacha_count * 150
        sql_info = pickle.dumps(colle)
        if mem_exists:
            db.execute("UPDATE Colle SET colle = ?, hiishi = ?, remain_jewel = ?, used_jewel = ? WHERE qqid = ?",
                       (sql_info, hiishi, remain_jewel, used_jewel, qqid))
        else:
            db.execute("INSERT INTO Colle(qqid, colle, hiishi, remain_jewel, used_jewel, last_reincarnated_time, reincarnated_count) VALUES(?, ?, ?, ?, ?, ?, 0)",
                       (qqid, sql_info, hiishi, remain_jewel, used_jewel, int(time.time())))
        self.db_conn.commit()
        db.close()
        return "\n".join(msg)

    def reincarnated(self, qqid: int) -> str:
        """转生

        Args:
            qqid (int): 需要转生的用户 QQ 号

        Returns:
            str: 转生处理结果消息
        """
        db = self.db_conn.cursor()
        sql_info = list(db.execute(
            "SELECT last_reincarnated_time, reincarnated_count FROM Colle WHERE qqid = ?", (qqid,)))
        exists = (len(sql_info) == 1)
        last_reincarnated_time = 0
        reincarnated_count = 0
        if exists:
            last_reincarnated_time = sql_info[0][0]
            reincarnated_count = sql_info[0][1]
        delta = time.time() - last_reincarnated_time
        if delta < 60 * 60 * 12:
            db.close()
            delta = 60 * 60 * 12 - delta
            hour = int(delta // 60 // 60)
            minute = int((delta - hour * 60 * 60) // 60)
            return f"[CQ:at,qq={qqid}]，转生正在 CD，请 {hour} 小时 {minute} 分钟后再来。"
        else:
            colle = pickle.dumps([])
            if exists:
                db.execute("UPDATE Colle SET colle = ?, hiishi = 0, remain_jewel = ?, used_jewel = 0, last_reincarnated_time = ?, reincarnated_count = reincarnated_count + 1 WHERE qqid = ?",
                           (colle, self.new_jewels_count, int(time.time()), qqid))
            else:
                db.execute("INSERT INTO Colle(qqid, colle, hiishi, remain_jewel, used_jewel, last_reincarnated_time, reincarnated_count) VALUES(?, ?, 0, ?, 0, ?, 1)",
                           (qqid, colle, self.new_jewels_count, int(time.time())))
            self.db_conn.commit()
            db.close()
            return f"[CQ:at,qq={qqid}]，这是你的第 {reincarnated_count + 1} 次转生。转生后的你已经是一条欧鳇了。"

    def check_collect(self, qqid: int) -> str:
        """查看仓库

        Args:
            qqid (int): 要查看仓库的用户 QQ 号

        Returns:
            str: 仓库内容
        """
        db = self.db_conn.cursor()
        sql_info = list(db.execute(
            "SELECT colle, hiishi, remain_jewel, used_jewel FROM Colle WHERE qqid=?", (qqid,)))
        mem_exists = (len(sql_info) == 1)
        colle = []
        hiishi = 0
        remain_jewel = self.new_jewels_count
        used_jewel = 0
        if mem_exists:
            colle = pickle.loads(sql_info[0][0])
            hiishi = sql_info[0][1]
            remain_jewel = sql_info[0][2]
            used_jewel = sql_info[0][3]
        else:
            db.execute("INSERT INTO Colle(qqid, colle, hiishi, remain_jewel, used_jewel, last_reincarnated_time, reincarnated_count) VALUES(?, ?, 0, ?, 0, ?, 0)",
                       (qqid, pickle.dumps([]), self.new_jewels_count, int(time.time())))

        charas = [["可可萝", "凯露", "佩可莉姆", "优衣"], [], []]
        for x in colle:
            charas[x[1] - 1].append(x[0])
        msg = []
        msg.append(f"[CQ:at,qq={qqid}]，您的仓库如下：")
        msg.append(f"{STAR_EMOJI_STR * 3}×{len(charas[2])}：")
        msg.append("、".join(charas[2]))
        msg.append(f"{STAR_EMOJI_STR * 2}×{len(charas[1])}：")
        msg.append("、".join(charas[1]))
        msg.append(f"{STAR_EMOJI_STR}×{len(charas[0])}：")
        msg.append("、".join(charas[0]))
        msg.append(f"🔮×{hiishi}，💎×{remain_jewel}")
        msg.append(f"历史消耗💎×{used_jewel}")
        return "\n".join(msg)

    def check_all_pools(self) -> str:
        """查看所有卡池

        Returns:
            str: 当前所有卡池的相关信息
        """
        msg = ["当前所有卡池如下："]
        for idx, x in enumerate(self.gacha_mgr.pools):
            msg.append("{}. {} {}".format(idx + 1, x.name, "" if x.describe ==
                                          "" or x.describe is None else f"（{x.describe}）"))
        return "\n".join(msg)

    def check_pool(self, gacha_name: Union[str, None] = None) -> str:
        """查看卡池指令

        Args:
            gacha_name (Union[str, None], optional): 需要查看的卡池名称，为 None 或空字符串时转入查看所有卡池

        Returns:
            str: 相关卡池信息
        """
        msg = []
        if gacha_name == "":
            return self.check_all_pools()
        else:
            pool = self.gacha_mgr.get_pool(gacha_name)
            if pool is not None:
                return pool.get_pool_info()
            else:
                return f"没有找到卡池：{gacha_name}！"
        return "\n".join(msg)

    def recharge(self, from_qqid: int, to_qqid: Union[int, None], add_jewel: int) -> str:
        """充值钻石

        Args:
            from_qqid (int): 进行充值操作的用户 QQ 号
            to_qqid (Union[int, None]): 需充值钻石的用户 QQ 号，为 None 时代表为曾经使用过抽卡系统的所有用户充值
            add_jewel (int): 充值的钻石数量

        Returns:
            str: 充值结果
        """
        if from_qqid not in self.admin_list:
            return f"[CQ:at,qq={from_qqid}]，您无权执行充值操作。"
        else:
            db = self.db_conn.cursor()
            if to_qqid is None:
                db.execute(
                    "UPDATE Colle SET remain_jewel = remain_jewel + ?", (add_jewel,))
                self.db_conn.commit()
                db.close()
                return f"成功为全服发放💎×{add_jewel}"
            else:
                sql = list(db.execute(
                    "SELECT remain_jewel FROM Colle WHERE qqid = ?", (int(to_qqid),)))
                exists = (len(sql) == 1)
                remain_jewel = self.new_jewels_count
                if not exists:
                    remain_jewel += add_jewel
                    db.execute("INSERT INTO Colle(qqid, colle, hiishi, remain_jewel, used_jewel, last_reincarnated_time, reincarnated_count) VALUES(?, ?, 0, ?, 0, ?, 0)",
                               (to_qqid, pickle.dumps([]), remain_jewel, int(time.time())))
                else:
                    remain_jewel = sql[0][0] + add_jewel
                    db.execute(
                        "UPDATE Colle SET remain_jewel = remain_jewel + ? WHERE qqid = ?", (add_jewel, int(to_qqid)))
                self.db_conn.commit()
                db.close()
                return f"成功为 [CQ:at,qq={to_qqid}] 充值💎×{add_jewel}，剩余💎×{remain_jewel}"

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        if not self.active:
            return
        if ((ctx["message_type"] == "group" and not self.setting.get("gacha_on", True))
                or (ctx["message_type"] == "private" and not self.setting.get("gacha_private_on", True))):
            return
        msg = ctx['raw_message']
        sender_qqid = ctx["user_id"]
        regex = [
            r"^(单抽|十连|抽一井|查看卡池) *(\S*)?$",
            r"^(仓库) *(?:\[CQ:at,qq=(\d+)\])? *$",
            r"^(转生) *$",
            r"^(充值) *(-?\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *$",
            r"^(全服送钻) *(-?\d+)([Ww万Kk千])? *$"
        ]
        match = None
        for r in regex:
            match = re.match(r, msg)
            if match is not None:
                break
        if match is None:
            return
        cmd = match.group(1)
        if cmd == "单抽":
            return self.gacha(sender_qqid, match.group(2), 1)
        elif cmd == "十连":
            return self.gacha(sender_qqid, match.group(2), 10)
        elif cmd == "抽一井":
            return self.gacha(sender_qqid, match.group(2), 300)
        elif cmd == "查看卡池":
            return self.check_pool(match.group(2))
        elif cmd == "仓库":
            if match.group(2) is not None:
                return self.check_collect(int(match.group(2)))
            else:
                return self.check_collect(sender_qqid)
        elif cmd == "转生":
            return self.reincarnated(sender_qqid)
        elif cmd == "充值" or cmd == "全服送钻":
            unit = {
                'W': 10000,
                'w': 10000,
                '万': 10000,
                'k': 1000,
                'K': 1000,
                '千': 1000,
            }.get(match.group(3), 1)
            add_jewel = int(match.group(2)) * unit
            if cmd == "充值":
                if match.group(4) is None:
                    return self.recharge(sender_qqid, sender_qqid, add_jewel)
                else:
                    return self.recharge(sender_qqid, int(match.group(4)), add_jewel)
            elif cmd == "全服送钻":
                return self.recharge(sender_qqid, None, add_jewel)
