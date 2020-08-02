import asyncio
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import peewee
from aiocqhttp.api import Api
from apscheduler.triggers.cron import CronTrigger
from quart import (Quart, jsonify, make_response, redirect, request, session,
                   url_for)

from ..templating import render_template
from ..web_util import async_cached_func
from ..ybdata import (Clan_challenge, Clan_group, Clan_member, Clan_subscribe,
                      User)
from .exception import (
    ClanBattleError, GroupError, GroupNotExist, InputError, UserError,
    UserNotInGroup)
from .typing import BossStatus, ClanBattleReport, Groupid, Pcr_date, QQid
from .util import atqq, pcr_datetime, pcr_timestamp, timed_cached_func

_logger = logging.getLogger(__name__)


class ClanBattle:
    Passive = True
    Active = True
    Request = True

    Commands = {
        '创建': 1,
        '加入': 2,
        '状态': 3,
        '报刀': 4,
        '尾刀': 5,
        '撤销': 6,
        '修正': 7,
        '修改': 7,
        '选择': 8,
        '切换': 8,
        '报告': 9,
        '查刀': 9,
        '预约': 10,
        '挂树': 11,
        '申请': 12,
        '锁定': 12,
        '取消': 13,
        '解锁': 14,
        '面板': 15,
        '后台': 15,
        'sl': 16,
        'SL': 16,
        '查树': 20,
        '查1': 21,
        '查2': 22,
        '查3': 23,
        '查4': 24,
        '查5': 25,
    }

    Server = {
        '日': 'jp',
        '台': 'tw',
        '韩': 'kr',
        '国': 'cn',
    }

    def __init__(self,
                 glo_setting: Dict[str, Any],
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.bossinfo = glo_setting['boss']
        self.api = bot_api

        # log
        if not os.path.exists(os.path.join(glo_setting['dirname'], 'log')):
            os.mkdir(os.path.join(glo_setting['dirname'], 'log'))

        formater = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s')
        filehandler = logging.FileHandler(
            os.path.join(glo_setting['dirname'], 'log', '公会战日志.log'),
            encoding='utf-8',
        )
        filehandler.setFormatter(formater)
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(formater)
        _logger.addHandler(filehandler)
        _logger.addHandler(consolehandler)
        _logger.setLevel(logging.INFO)

        # data initialize
        self._boss_status: Dict[str, asyncio.Future] = {}

        for group in Clan_group.select().where(
            Clan_group.deleted == False,
        ):
            self._boss_status[group.group_id] = (
                asyncio.get_event_loop().create_future()
            )

        # super-admin initialize
        User.update({User.authority_group: 100}).where(
            User.authority_group == 1
        ).execute()
        User.update({User.authority_group: 1}).where(
            User.qqid.in_(self.setting['super-admin'])
        ).execute()

    def _level_by_cycle(self, cycle, *, level_4=None, game_server=None):
        if cycle <= 3:
            return 0
        elif cycle <= 10:
            return 1
        else:
            if level_4 is None:
                level_4 = (len(self.setting['boss'][game_server]) == 4)
            if level_4 and cycle >= 35:
                return 3
            return 2

    @timed_cached_func(128, 3600, ignore_self=True)
    def _get_nickname_by_qqid(self, qqid) -> Union[str, None]:
        user = User.get_or_create(qqid=qqid)[0]
        if user.nickname is None:
            asyncio.ensure_future(self._update_user_nickname_async(
                qqid=qqid,
                group_id=None,
            ))
        return user.nickname or str(qqid)

    def _get_group_previous_challenge(self, group: Clan_group):
        Clan_challenge_alias = Clan_challenge.alias()
        query = Clan_challenge.select().where(
            Clan_challenge.cid == Clan_challenge_alias.select(
                peewee.fn.MAX(Clan_challenge_alias.cid)
            ).where(
                Clan_challenge_alias.gid == group.group_id,
                Clan_challenge_alias.bid == group.battle_id,
            )
        )
        try:
            return query.get()
        except peewee.DoesNotExist:
            return None

    async def _update_group_list_async(self):
        try:
            group_list = await self.api.get_group_list()
        except Exception as e:
            _logger.exception('获取群列表错误'+str(e))
            return False
        for group_info in group_list:
            group = Clan_group.get_or_none(
                group_id=group_info['group_id'],
            )
            if group is None:
                continue
            group.group_name = group_info['group_name']
            group.save()
        return True

    @async_cached_func(16)
    async def _fetch_member_list_async(self, group_id):
        try:
            group_member_list = await self.api.get_group_member_list(group_id=group_id)
        except Exception as e:
            _logger.exception('获取群成员列表错误'+str(type(e))+str(e))
            asyncio.ensure_future(self.api.send_group_msg(
                group_id=group_id, message='获取群成员错误，这可能是缓存问题，请重启酷Q后再试'))
            return []
        return group_member_list

    async def _update_all_group_members_async(self, group_id):
        group_member_list = await self._fetch_member_list_async(group_id)
        for member in group_member_list:
            user = User.get_or_create(qqid=member['user_id'])[0]
            membership = Clan_member.get_or_create(
                group_id=group_id, qqid=member['user_id'])[0]
            user.nickname = member.get('card') or member['nickname']
            user.clan_group_id = group_id
            if user.authority_group >= 10:
                user.authority_group = (
                    100 if member['role'] == 'member' else 10)
                membership.role = user.authority_group
            user.save()
            membership.save()

        # refresh member list
        self.get_member_list(group_id, nocache=True)

    async def _update_user_nickname_async(self, qqid, group_id=None):
        try:
            user = User.get_or_create(qqid=qqid)[0]
            if group_id is None:
                userinfo = await self.api.get_stranger_info(user_id=qqid)
                user.nickname = userinfo['nickname']
            else:
                userinfo = await self.api.get_group_member_info(
                    group_id=group_id, user_id=qqid)
                user.nickname = userinfo['card'] or userinfo['nickname']
            user.save()

            # refresh
            if user.nickname is not None:
                self._get_nickname_by_qqid(qqid, nocache=True)
        except Exception as e:
            _logger.exception(e)

    def _boss_data_dict(self, group: Clan_group) -> Dict[str, Any]:
        return {
            'cycle': group.boss_cycle,
            'num': group.boss_num,
            'health': group.boss_health,
            'challenger': group.challenging_member_qq_id,
            'lock_type': group.boss_lock_type,
            'challenging_comment': group.challenging_comment,
            'full_health': (
                self.bossinfo[group.game_server]
                [self._level_by_cycle(
                    group.boss_cycle, game_server=group.game_server)]
                [group.boss_num-1]
            ),
        }

    def creat_group(self, group_id: Groupid, game_server, group_name=None) -> None:
        """
        create a group for clan-battle

        Args:
            group_id: group id
            game_server: name of game server("jp" "tw" "cn" "kr")
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            group = Clan_group.create(
                group_id=group_id,
                group_name=group_name,
                game_server=game_server,
                boss_health=self.bossinfo[game_server][0][0],
            )
        elif group.deleted:
            group.deleted = False
            group.game_server = game_server
            group.save()
        else:
            raise GroupError('群已经存在')
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()

        # refresh group list
        asyncio.ensure_future(self._update_group_list_async())

    async def bind_group(self, group_id: Groupid, qqid: QQid, nickname: str):
        """
        set user's default group

        Args:
            group_id: group id
            qqid: qqid
            nickname: displayed name
        """
        user = User.get_or_create(qqid=qqid)[0]
        user.clan_group_id = group_id
        user.nickname = nickname
        user.deleted = False
        try:
            groupmember = await self.api.get_group_member_info(
                group_id=group_id, user_id=qqid)
            role = 100 if groupmember['role'] == 'member' else 10
        except Exception as e:
            _logger.exception(e)
            role = 100
        membership = Clan_member.get_or_create(
            group_id=group_id,
            qqid=qqid,
            defaults={
                'role': role,
            }
        )[0]
        user.save()

        # refresh
        self.get_member_list(group_id, nocache=True)
        if nickname is None:
            asyncio.ensure_future(self._update_user_nickname_async(
                qqid=qqid,
                group_id=group_id,
            ))

        return membership

    def drop_member(self, group_id: Groupid, member_list: List[QQid]):
        """
        delete members from group member list

        permission should be checked before this function is called.

        Args:
            group_id: group id
            member_list: a list of qqid to delete
        """
        delete_count = Clan_member.delete().where(
            Clan_member.group_id == group_id,
            Clan_member.qqid.in_(member_list)
        ).execute()

        for user_id in member_list:
            user = User.get_or_none(qqid=user_id)
            if user is not None:
                user.clan_group_id = None
                user.save()

        # refresh member list
        self.get_member_list(group_id, nocache=True)
        return delete_count

    def boss_status_summary(self, group_id: Groupid) -> str:
        """
        get a summary of boss status

        Args:
            group_id: group id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        boss_summary = (
            f'现在{group.boss_cycle}周目，{group.boss_num}号boss\n'
            f'生命值{group.boss_health:,}'
        )
        if group.challenging_member_qq_id is not None:
            action = '正在挑战' if group.boss_lock_type == 1 else '锁定了'
            boss_summary += '\n{}{}boss'.format(
                self._get_nickname_by_qqid(group.challenging_member_qq_id)
                or group.challenging_member_qq_id,
                action,
            )
            if group.boss_lock_type != 1:
                boss_summary += '\n留言：'+group.challenging_comment
        return boss_summary

    def challenge(self,
                  group_id: Groupid,
                  qqid: QQid,
                  defeat: bool,
                  damage: Optional[int] = None,
                  behalfed: Optional[QQid] = None,
                  *,
                  extra_msg: Optional[str] = None,
                  previous_day=False,
                  ) -> BossStatus:
        """
        record a non-defeat challenge to boss

        Args:
            group_id: group id
            qqid: qqid of member who do the record
            damage: the damage dealt to boss
            behalfed: the real member who did the challenge
        """
        if (not defeat) and (damage is None):
            raise InputError('未击败boss需要提供伤害值')
        if (not defeat) and (damage < 0):
            raise InputError('伤害不可以是负数')
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        if (not defeat) and (damage >= group.boss_health):
            raise InputError('伤害超出剩余血量，如击败请使用尾刀')
        behalf = None
        if behalfed is not None:
            behalf = qqid
            qqid = behalfed
        user = User.get_or_create(
            qqid=qqid,
            defaults={
                'clan_group_id': group_id,
            }
        )[0]
        is_member = Clan_member.get_or_none(
            group_id=group_id, qqid=qqid)
        if not is_member:
            raise UserNotInGroup
        d, t = pcr_datetime(area=group.game_server)
        if previous_day:
            today_count = Clan_challenge.select().where(
                Clan_challenge.gid == group_id,
                Clan_challenge.bid == group.battle_id,
                Clan_challenge.challenge_pcrdate == d,
            ).count()
            if today_count != 0:
                raise GroupError('今日报刀记录不为空，无法将记录添加到昨日')
            d -= 1
            t += 86400
        challenges = Clan_challenge.select().where(
            Clan_challenge.gid == group_id,
            Clan_challenge.qqid == qqid,
            Clan_challenge.bid == group.battle_id,
            Clan_challenge.challenge_pcrdate == d,
        ).order_by(Clan_challenge.cid)
        challenges = list(challenges)
        finished = sum(bool(c.boss_health_ramain or c.is_continue)
                       for c in challenges)
        if finished >= 3:
            if previous_day:
                raise InputError('昨日上报次数已达到3次')
            raise InputError('今日上报次数已达到3次')
        is_continue = (challenges
                       and challenges[-1].boss_health_ramain == 0
                       and not challenges[-1].is_continue)
        is_member.last_message = extra_msg
        is_member.save()
        if defeat:
            boss_health_ramain = 0
            challenge_damage = group.boss_health
        else:
            boss_health_ramain = group.boss_health-damage
            challenge_damage = damage
        challenge = Clan_challenge.create(
            gid=group_id,
            qqid=user.qqid,
            bid=group.battle_id,
            challenge_pcrdate=d,
            challenge_pcrtime=t,
            boss_cycle=group.boss_cycle,
            boss_num=group.boss_num,
            boss_health_ramain=boss_health_ramain,
            challenge_damage=challenge_damage,
            is_continue=is_continue,
            message=extra_msg,
            behalf=behalf,
        )
        if defeat:
            if group.boss_num == 5:
                group.boss_num = 1
                group.boss_cycle += 1
            else:
                group.boss_num += 1
            health_before = group.boss_health
            group.boss_health = (
                self.bossinfo[group.game_server]
                [self._level_by_cycle(
                    group.boss_cycle, game_server=group.game_server)]
                [group.boss_num-1])
        else:
            group.boss_health -= damage
        # 如果当前正在挑战，则取消挑战
        if user.qqid == group.challenging_member_qq_id:
            group.challenging_member_qq_id = None
        # 如果当前正在挂树，则取消挂树
        Clan_subscribe.delete().where(
            Clan_subscribe.gid == group_id,
            Clan_subscribe.qqid == qqid,
            Clan_subscribe.subscribe_item == 0,
        ).execute()

        challenge.save()
        group.save()

        nik = user.nickname or user.qqid
        if defeat:
            msg = '{}对boss造成了{:,}点伤害，击败了boss\n（今日第{}刀，{}）'.format(
                nik, health_before, finished+1, '尾余刀' if is_continue else '收尾刀'
            )
        else:
            msg = '{}对boss造成了{:,}点伤害\n（今日第{}刀，{}）'.format(
                nik, damage, finished+1, '剩余刀' if is_continue else '完整刀'
            )
        status = BossStatus(
            group.boss_cycle,
            group.boss_num,
            group.boss_health,
            0,
            msg,
        )
        self._boss_status[group_id].set_result(
            (self._boss_data_dict(group), msg)
        )
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()

        if defeat:
            self.notify_subscribe(group_id, group.boss_num)

        return status

    def undo(self, group_id: Groupid, qqid: QQid) -> BossStatus:
        """
        rollback last challenge record.

        Args:
            group_id: group id
            qqid: qqid of member who ask for the undo
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        user = User.get_or_create(
            qqid=qqid,
            defaults={
                'clan_group_id': group_id,
            }
        )[0]
        last_challenge = self._get_group_previous_challenge(group)
        if last_challenge is None:
            raise GroupError('本群无出刀记录')
        if (last_challenge.qqid != qqid) and (user.authority_group >= 100):
            raise UserError('无权撤销')
        group.boss_cycle = last_challenge.boss_cycle
        group.boss_num = last_challenge.boss_num
        group.boss_health = (last_challenge.boss_health_ramain
                             + last_challenge.challenge_damage)
        last_challenge.delete_instance()
        group.save()

        nik = self._get_nickname_by_qqid(last_challenge.qqid)
        status = BossStatus(
            group.boss_cycle,
            group.boss_num,
            group.boss_health,
            0,
            f'{nik}的出刀记录已被撤销',
        )
        self._boss_status[group_id].set_result(
            (self._boss_data_dict(group), status.info)
        )
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()
        return status

    def modify(self, group_id: Groupid, cycle=None, boss_num=None, boss_health=None):
        """
        modify status of boss.

        permission should be checked before this function is called.

        Args:
            group_id: group id
            cycle: new number of clan-battle cycle
            boss_num: new number of boss
            boss_health: new value of boss health
        """
        if cycle and cycle < 1:
            raise InputError('周目数不能为负')
        if boss_num and (boss_num < 1 or boss_num > 5):
            raise InputError('boss编号必须在1~5间')
        if boss_health and boss_health < 1:
            raise InputError('boss生命值不能为负')
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        if cycle is not None:
            group.boss_cycle = cycle
        if boss_num is not None:
            group.boss_num = boss_num
        if boss_health is None:
            boss_health = (
                self.bossinfo[group.game_server]
                [self._level_by_cycle(
                    group.boss_cycle, game_server=group.game_server)]
                [group.boss_num-1])
        group.boss_health = boss_health
        group.save()

        status = BossStatus(
            group.boss_cycle,
            group.boss_num,
            group.boss_health,
            0,
            'boss状态已修改',
        )
        self._boss_status[group_id].set_result(
            (self._boss_data_dict(group), status.info)
        )
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()
        return status

    def change_game_server(self, group_id: Groupid, game_server):
        """
        change game server.

        permission should be checked before this function is called.

        Args:
            group_id: group id
            game_server: name of game server("jp" "tw" "cn" "kr")
        """
        if game_server not in ("jp", "tw", "cn", "kr"):
            raise InputError(f'不存在{game_server}游戏服务器')
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        group.game_server = game_server
        group.save()

    def get_data_slot_record_count(self, group_id: Groupid):
        """
        creat new new_data_slot for challenge data and reset boss status.

        challenge data should be backuped and comfirm and
        permission should be checked before this function is called.

        Args:
            group_id: group id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        counts = []
        for c in Clan_challenge.select(
            Clan_challenge.bid,
            peewee.fn.COUNT(Clan_challenge.cid).alias('record_count'),
        ).where(
            Clan_challenge.gid == group_id
        ).group_by(
            Clan_challenge.bid,
        ):
            counts.append({
                'battle_id': c.bid,
                'record_count': c.record_count,
            })
        return counts

    # def new_data_slot(self, group_id: Groupid):
    #     """
    #     creat new new_data_slot for challenge data and reset boss status.

    #     challenge data should be backuped and comfirm and
    #     permission should be checked before this function is called.

    #     Args:
    #         group_id: group id
    #     """
    #     group = Clan_group.get_or_none(group_id=group_id)
    #     if group is None:
    #         raise GroupNotExist
    #     group.boss_cycle = 1
    #     group.boss_num = 1
    #     group.boss_health = self.bossinfo[group.game_server][0][0]
    #     group.battle_id += 1
    #     group.save()
    #     Clan_subscribe.delete().where(
    #         Clan_subscribe.gid == group_id,
    #     ).execute()

    def clear_data_slot(self, group_id: Groupid, battle_id: Optional[int] = None):
        """
        clear data_slot for challenge data and reset boss status.

        challenge data should be backuped and comfirm and
        permission should be checked before this function is called.

        Args:
            group_id: group id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        group.boss_cycle = 1
        group.boss_num = 1
        group.boss_health = self.bossinfo[group.game_server][0][0]
        group.challenging_member_qq_id = None
        group.save()
        if battle_id is None:
            battle_id = group.battle_id
        Clan_challenge.delete().where(
            Clan_challenge.gid == group_id,
            Clan_challenge.bid == battle_id,
        ).execute()
        Clan_subscribe.delete().where(
            Clan_subscribe.gid == group_id,
        ).execute()
        _logger.info(f'群{group_id}的{battle_id}号存档已清空')

    def switch_data_slot(self, group_id: Groupid, battle_id: int):
        """
        switch data_slot for challenge data and reset boss status.

        challenge data should be backuped and comfirm and
        permission should be checked before this function is called.

        Args:
            group_id: group id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        group.battle_id = battle_id
        last_challenge = self._get_group_previous_challenge(group)
        if last_challenge is None:
            group.boss_cycle = 1
            group.boss_num = 1
            group.boss_health = self.bossinfo[group.game_server][0][0]
        else:
            group.boss_cycle = last_challenge.boss_cycle
            group.boss_num = last_challenge.boss_num
            group.boss_health = last_challenge.boss_health_ramain
            if group.boss_health == 0:
                if group.boss_num == 5:
                    group.boss_num = 1
                    group.boss_cycle += 1
                else:
                    group.boss_num += 1
                group.boss_health = (
                    self.bossinfo[group.game_server]
                    [self._level_by_cycle(
                        group.boss_cycle, game_server=group.game_server)]
                    [group.boss_num-1])
        group.challenging_member_qq_id = None
        group.save()
        Clan_subscribe.delete().where(
            Clan_subscribe.gid == group_id,
        ).execute()
        _logger.info(f'群{group_id}切换至{battle_id}号存档')

    async def send_private_remind(self, member_list: List[QQid], content: str):
        for qqid in member_list:
            await asyncio.sleep(random.randint(3, 10))
            try:
                await self.api.send_private_msg(user_id=qqid, message=content)
                _logger.info(f'向{qqid}发送出刀提醒')
            except Exception as e:
                _logger.exception(e)

    def send_remind(self,
                    group_id: Groupid,
                    member_list: List[QQid],
                    sender: QQid,
                    send_private_msg: bool = False):
        """
        remind members to finish challenge

        permission should be checked before this function is called.

        Args:
            group_id: group id
            member_list: a list of qqid to reminder
        """
        sender_name = self._get_nickname_by_qqid(sender)
        if send_private_msg:
            asyncio.ensure_future(self.send_private_remind(
                member_list=member_list,
                content=f'{sender_name}提醒您及时完成今日出刀',
            ))
        else:
            message = ' '.join((
                atqq(qqid) for qqid in member_list
            ))
            asyncio.ensure_future(self.api.send_group_msg(
                group_id=group_id,
                message=message+f'\n=======\n{sender_name}提醒您及时完成今日出刀',
            ))

    def add_subscribe(self, group_id: Groupid, qqid: QQid, boss_num, message=None):
        """
        subscribe a boss, get notification when boss is defeated.

        subscribe for all boss when `boss_num` is `0`

        Args:
            group_id: group id
            qqid: qq id of subscriber
            boss_num: number of boss to subscribe, `0` for all
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        user = User.get_or_none(qqid=qqid)
        if user is None:
            raise GroupError('请先加入公会')
        subscribe = Clan_subscribe.get_or_none(
            gid=group_id,
            qqid=qqid,
            subscribe_item=boss_num,
        )
        if subscribe is not None:
            if boss_num == 0:
                raise UserError('您已经在树上了')
            raise UserError('您已经预约过了')
        if (boss_num == 0 and group.challenging_member_qq_id == qqid):
            # 如果挂树时当前正在挑战，则取消挑战
            group.challenging_member_qq_id = None
            group.save()
        subscribe = Clan_subscribe.create(
            gid=group_id,
            qqid=qqid,
            subscribe_item=boss_num,
            message=message,
        )

    def get_subscribe_list(self, group_id: Groupid, boss_num=None) -> List[Tuple[int, QQid, dict]]:
        """
        get the subscribe lists.

        return a list of subscribe infomation,
        each item is a tuple of (boss_id, qq_id, message)

        Args:
            group_id: group id
        """
        subscribe_list = []
        query = [Clan_subscribe.gid == group_id]
        if boss_num is not None:
            query.append(Clan_subscribe.subscribe_item == boss_num)
        for subscribe in Clan_subscribe.select().where(
            *query
        ).order_by(
            Clan_subscribe.sid
        ):
            subscribe_list.append({
                'boss': subscribe.subscribe_item,
                'qqid': subscribe.qqid,
                'message': subscribe.message,
            })
        return subscribe_list

    def cancel_subscribe(self, group_id: Groupid, qqid: QQid, boss_num) -> int:
        """
        cancel a subscription.

        Args:
            group_id: group id
            qqid: qq id of subscriber
            boss_num: number of boss to be canceled
        """
        deleted_counts = Clan_subscribe.delete().where(
            Clan_subscribe.gid == group_id,
            Clan_subscribe.qqid == qqid,
            Clan_subscribe.subscribe_item == boss_num,
        ).execute()
        return deleted_counts

    def notify_subscribe(self, group_id: Groupid, boss_num=None, send_private_msg=False):
        """
        send notification to subsciber and remove them (when boss is defeated).

        Args:
            group_id: group id
            boss_num: number of new boss
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        if boss_num is None:
            boss_num = group.boss_num
        notice = []
        for subscribe in Clan_subscribe.select().where(
            Clan_subscribe.gid == group_id,
            (Clan_subscribe.subscribe_item == boss_num) |
            (Clan_subscribe.subscribe_item == 0),
        ).order_by(Clan_subscribe.sid):
            msg = atqq(subscribe.qqid)
            if subscribe.message:
                msg += subscribe.message
            notice.append(msg)
            subscribe.delete_instance()
        if notice:
            asyncio.ensure_future(self.api.send_group_msg(
                group_id=group_id,
                message='boss已被击败\n'+'\n'.join(notice),
            ))

    def apply_for_challenge(self,
                            group_id: Groupid,
                            qqid: QQid,
                            *,
                            extra_msg: Optional[str] = None,
                            appli_type: int = 0,
                            ) -> BossStatus:
        """
        apply for a challenge to boss.

        Args:
            group_id: group id
            qqid: qq id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        user = User.get_or_none(qqid=qqid)
        if user is None:
            raise UserNotInGroup
        if (appli_type != 1) and (extra_msg is None):
            raise InputError('锁定boss时必须留言')
        if group.challenging_member_qq_id is not None:
            nik = self._get_nickname_by_qqid(
                group.challenging_member_qq_id,
            ) or group.challenging_member_qq_id
            action = '正在挑战' if group.boss_lock_type == 1 else '锁定了'
            msg = f'申请失败，{nik}{action}boss'
            if group.boss_lock_type != 1:
                msg += '\n留言：'+group.challenging_comment
            raise GroupError(msg)
        group.challenging_member_qq_id = qqid
        group.challenging_start_time = int(time.time())
        group.challenging_comment = extra_msg
        group.boss_lock_type = appli_type
        group.save()

        nik = self._get_nickname_by_qqid(qqid) or qqid
        info = (f'{nik}已开始挑战boss' if appli_type == 1 else
                f'{nik}锁定了boss\n留言：{extra_msg}')
        status = BossStatus(
            group.boss_cycle,
            group.boss_num,
            group.boss_health,
            qqid,
            info,
        )
        self._boss_status[group_id].set_result(
            (self._boss_data_dict(group), status.info)
        )
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()
        return status

    def cancel_application(self, group_id: Groupid, qqid: QQid) -> BossStatus:
        """
        cancel a application of boss challenge 3 minutes after the challenge starts.

        Args:
            group_id: group id
            qqid: qq id of the canceler
            force_cancel: ignore the 3-minutes restriction
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        if group.challenging_member_qq_id is None:
            raise GroupError('boss没有锁定')
        user = User.get_or_create(
            qqid=qqid,
            defaults={
                'clan_group_id': group_id,
            }
        )[0]
        if (group.challenging_member_qq_id != qqid) and (user.authority_group >= 100):
            challenge_duration = (int(time.time())
                                  - group.challenging_start_time)
            is_challenge = (group.boss_lock_type == 1)
            if (not is_challenge) or (challenge_duration < 180):
                nik = self._get_nickname_by_qqid(
                    group.challenging_member_qq_id,
                ) or group.challenging_member_qq_id
                msg = f'失败，{nik}在{challenge_duration}秒前'+(
                    '开始挑战boss' if is_challenge else
                    ('锁定了boss\n留言：'+group.challenging_comment)
                )
                raise GroupError(msg)
        group.challenging_member_qq_id = None
        group.save()

        status = BossStatus(
            group.boss_cycle,
            group.boss_num,
            group.boss_health,
            0,
            'boss挑战已可申请',
        )
        self._boss_status[group_id].set_result(
            (self._boss_data_dict(group), status.info)
        )
        self._boss_status[group_id] = asyncio.get_event_loop().create_future()
        return status

    def save_slot(self, group_id: Groupid, qqid: QQid, todaystatus: bool = True, only_check: bool = False):
        """
        record today's save slot

        Args:
            group_id: group id
            qqid: qqid of member who do the record
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        membership = Clan_member.get_or_none(
            group_id=group_id, qqid=qqid)
        if membership is None:
            raise UserNotInGroup
        today, _ = pcr_datetime(group.game_server)
        if only_check:
            return (membership.last_save_slot == today)
        if todaystatus:
            if membership.last_save_slot == today:
                raise UserError('您今天已经存在SL记录了')
            membership.last_save_slot = today

            # 如果当前正在挑战，则取消挑战
            if (group.challenging_member_qq_id == qqid):
                group.challenging_member_qq_id = None
                group.save()
            # 如果当前正在挂树，则取消挂树
            Clan_subscribe.delete().where(
                Clan_subscribe.gid == group_id,
                Clan_subscribe.qqid == qqid,
                Clan_subscribe.subscribe_item == 0,
            ).execute()
        else:
            if membership.last_save_slot != today:
                raise UserError('您今天没有SL记录')
            membership.last_save_slot = 0
        membership.save()

        # refresh
        self.get_member_list(group_id, nocache=True)

        return todaystatus

    @timed_cached_func(max_len=64, max_age_seconds=10, ignore_self=True)
    def get_report(self,
                   group_id: Groupid,
                   battle_id: Union[str, int, None],
                   qqid: Optional[QQid] = None,
                   pcrdate: Optional[Pcr_date] = None,
                   # start_time: Optional[Pcr_time] = None,
                   # end_time: Optional[Pcr_time] = None,
                   ) -> ClanBattleReport:
        """
        get the records

        Args:
            group_id: group id
            qqid: user id of report
            pcrdate: pcrdate of report
            start_time: start time of report
            end_time: end time of report
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        report = []
        expressions = [
            Clan_challenge.gid == group_id,
        ]
        if battle_id is None:
            battle_id = group.battle_id
        if isinstance(battle_id, str):
            if battle_id == 'all':
                pass
            else:
                raise InputError(
                    f'unexceptd value "{battle_id}" for battle_id')
        else:
            expressions.append(Clan_challenge.bid == battle_id)
        if qqid is not None:
            expressions.append(Clan_challenge.qqid == qqid)
        if pcrdate is not None:
            expressions.append(Clan_challenge.challenge_pcrdate == pcrdate)
        # if start_time is not None:
        #     expressions.append(Clan_challenge.challenge_pcrtime >= start_time)
        # if end_time is not None:
        #     expressions.append(Clan_challenge.challenge_pcrtime <= end_time)
        for c in Clan_challenge.select().where(
            *expressions
        ):
            report.append({
                'battle_id': c.bid,
                'qqid': c.qqid,
                'challenge_time': pcr_timestamp(
                    c.challenge_pcrdate,
                    c.challenge_pcrtime,
                    group.game_server,
                ),
                'challenge_pcrdate': c.challenge_pcrdate,
                'challenge_pcrtime': c.challenge_pcrtime,
                'cycle': c.boss_cycle,
                'boss_num': c.boss_num,
                'health_ramain': c.boss_health_ramain,
                'damage': c.challenge_damage,
                'is_continue': c.is_continue,
                'message': c.message,
                'behalf': c.behalf,
            })
        return report

    @timed_cached_func(max_len=64, max_age_seconds=10, ignore_self=True)
    def get_battle_member_list(self,
                               group_id: Groupid,
                               battle_id: Union[str, int, None],
                               ):
        """
        get the member lists for clan-battle report

        return a list of member infomation,

        Args:
            group_id: group id
        """
        group = Clan_group.get_or_none(group_id=group_id)
        if group is None:
            raise GroupNotExist
        expressions = [
            Clan_challenge.gid == group_id,
        ]
        if battle_id is None:
            battle_id = group.battle_id
        if isinstance(battle_id, str):
            if battle_id == 'all':
                pass
            else:
                raise InputError(
                    f'unexceptd value "{battle_id}" for battle_id')
        else:
            expressions.append(Clan_challenge.bid == battle_id)
        member_list = []
        for u in Clan_challenge.select(
            Clan_challenge.qqid,
            User.nickname,
        ).join(
            User,
            on=(Clan_challenge.qqid == User.qqid),
            attr='user',
        ).where(
            *expressions
        ).distinct():
            member_list.append({
                'qqid': u.qqid,
                'nickname': u.user.nickname,
            })
        return member_list

    @timed_cached_func(max_len=16, max_age_seconds=3600, ignore_self=True)
    def get_member_list(self, group_id: Groupid) -> List[Dict[str, Any]]:
        """
        get the member lists from database

        return a list of member infomation,

        Args:
            group_id: group id
        """
        member_list = []
        for user in User.select(
            User, Clan_member,
        ).join(
            Clan_member,
            on=(User.qqid == Clan_member.qqid),
            attr='clan_member',
        ).where(
            Clan_member.group_id == group_id,
            User.deleted == False,
        ):
            member_list.append({
                'qqid': user.qqid,
                'nickname': user.nickname,
                'sl': user.clan_member.last_save_slot,
            })
        return member_list

    def jobs(self):
        trigger = CronTrigger(hour=5)

        def ensure_future_update_all_group_members():
            asyncio.ensure_future(self._update_group_list_async())

        return ((trigger, ensure_future_update_all_group_members),)

    def match(self, cmd):
        if self.setting['clan_battle_mode'] != 'web':
            return 0
        if len(cmd) < 2:
            return 0
        return self.Commands.get(cmd[0:2], 0)

    def execute(self, match_num, ctx):
        if ctx['message_type'] != 'group':
            return None
        cmd = ctx['raw_message']
        group_id = ctx['group_id']
        user_id = ctx['user_id']
        if match_num == 1:  # 创建
            match = re.match(r'^创建(?:([日台韩国])服)?[公工行]会$', cmd)
            if not match:
                return
            game_server = self.Server.get(match.group(1), 'cn')
            try:
                self.creat_group(group_id, game_server)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return ('公会创建成功，请登录后台查看，'
                    '公会战成员请发送“加入公会”，'
                    '或发送“加入全部成员”')
        elif match_num == 2:  # 加入
            if cmd == '加入全部成员':
                if ctx['sender']['role'] == 'member':
                    return '只有管理员才可以加入全部成员'
                _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
                asyncio.ensure_future(
                    self._update_all_group_members_async(group_id))
                return '本群所有成员已添加记录'
            match = re.match(r'^加入[公工行]会 *(?:\[CQ:at,qq=(\d+)\])? *$', cmd)
            if match:
                if match.group(1):
                    if ctx['sender']['role'] == 'member':
                        return '只有管理员才可以加入其他成员'
                    user_id = int(match.group(1))
                    nickname = None
                else:
                    nickname = (ctx['sender'].get('card')
                                or ctx['sender'].get('nickname'))
                asyncio.ensure_future(
                    self.bind_group(group_id, user_id, nickname))
                _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
                return '{}已加入本公会'.format(atqq(user_id))
        elif match_num == 3:  # 状态
            if cmd != '状态':
                return
            try:
                boss_summary = self.boss_status_summary(group_id)
            except ClanBattleError as e:
                return str(e)
            return boss_summary
        elif match_num == 4:  # 报刀
            match = re.match(
                r'^报刀 ?(\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *(昨[日天])? *(?:[\:：](.*))?$', cmd)
            if not match:
                return
            unit = {
                'W': 10000,
                'w': 10000,
                '万': 10000,
                'k': 1000,
                'K': 1000,
                '千': 1000,
            }.get(match.group(2), 1)
            damage = int(match.group(1)) * unit
            behalf = match.group(3) and int(match.group(3))
            previous_day = bool(match.group(4))
            extra_msg = match.group(5)
            if isinstance(extra_msg, str):
                extra_msg = extra_msg.strip()
                if not extra_msg:
                    extra_msg = None
            try:
                boss_status = self.challenge(
                    group_id,
                    user_id,
                    False,
                    damage,
                    behalf,
                    extra_msg=extra_msg,
                    previous_day=previous_day)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return str(boss_status)
        elif match_num == 5:  # 尾刀
            match = re.match(
                r'^尾刀 ?(?:\[CQ:at,qq=(\d+)\])? *(昨[日天])? *(?:[\:：](.*))?$', cmd)
            if not match:
                return
            behalf = match.group(1) and int(match.group(1))
            previous_day = bool(match.group(2))
            extra_msg = match.group(3)
            if isinstance(extra_msg, str):
                extra_msg = extra_msg.strip()
                if not extra_msg:
                    extra_msg = None
            try:
                boss_status = self.challenge(
                    group_id,
                    user_id,
                    True,
                    None,
                    behalf,
                    extra_msg=extra_msg,
                    previous_day=previous_day)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return str(boss_status)
        elif match_num == 6:  # 撤销
            if cmd != '撤销':
                return
            try:
                boss_status = self.undo(group_id, user_id)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return str(boss_status)
        elif match_num == 7:  # 修正
            if len(cmd) != 2:
                return
            url = urljoin(
                self.setting['public_address'],
                '{}clan/{}/'.format(
                    self.setting['public_basepath'],
                    group_id
                )
            )
            return '请登录面板操作：'+url
        elif match_num == 8:  # 选择
            if len(cmd) != 2:
                return
            url = urljoin(
                self.setting['public_address'],
                '{}clan/{}/setting/'.format(
                    self.setting['public_basepath'],
                    group_id
                )
            )
            return '请登录面板操作：'+url
        elif match_num == 9:  # 报告
            if len(cmd) != 2:
                return
            url = urljoin(
                self.setting['public_address'],
                '{}clan/{}/progress/'.format(
                    self.setting['public_basepath'],
                    group_id
                )
            )
            return '请在面板中查看：'+url
        elif match_num == 10:  # 预约
            match = re.match(r'^预约([1-5]) *(?:[\:：](.*))?$', cmd)
            if not match:
                return
            boss_num = int(match.group(1))
            extra_msg = match.group(2)
            if isinstance(extra_msg, str):
                extra_msg = extra_msg.strip()
                if not extra_msg:
                    extra_msg = None
            try:
                self.add_subscribe(group_id, user_id, boss_num, extra_msg)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return '预约成功'
        elif match_num == 11:  # 挂树
            match = re.match(r'^挂树 *(?:[\:：](.*))?$', cmd)
            if not match:
                return
            extra_msg = match.group(1)
            if isinstance(extra_msg, str):
                extra_msg = extra_msg.strip()
                if not extra_msg:
                    extra_msg = None
            try:
                self.add_subscribe(group_id, user_id, 0, extra_msg)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return '已挂树'
        elif match_num == 12:  # 申请/锁定
            if cmd == '申请出刀':
                appli_type = 1
                extra_msg = None
            elif cmd == '锁定':
                return '锁定时请留言'
            else:
                match = re.match(r'^锁定(?:boss)? *(?:[\:：](.*))?$', cmd)
                if not match:
                    return
                appli_type = 2
                extra_msg = match.group(1)
                if isinstance(extra_msg, str):
                    extra_msg = extra_msg.strip()
                    if not extra_msg:
                        return '锁定时请留言'
                else:
                    return
            try:
                boss_status = self.apply_for_challenge(
                    group_id, user_id, extra_msg=extra_msg, appli_type=appli_type)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return str(boss_status)
        elif match_num == 13:  # 取消
            match = re.match(r'^取消(?:预约)?([1-5]|挂树)$', cmd)
            if not match:
                return
            b = match.group(1)
            if b == '挂树':
                boss_num = 0
                event = b
            else:
                boss_num = int(b)
                event = f'预约{b}号boss'
            counts = self.cancel_subscribe(group_id, user_id, boss_num)
            if counts == 0:
                return '您没有'+event
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return '已取消'+event
        elif match_num == 14:  # 解锁
            if cmd != '解锁':
                return
            try:
                boss_status = self.cancel_application(group_id, user_id)
            except ClanBattleError as e:
                _logger.info('群聊 失败 {} {} {}'.format(user_id, group_id, cmd))
                return str(e)
            _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
            return str(boss_status)
        elif match_num == 15:  # 面板
            if len(cmd) != 2:
                return
            url = urljoin(
                self.setting['public_address'],
                '{}clan/{}/'.format(
                    self.setting['public_basepath'],
                    group_id
                )
            )
            return f'公会战面板：\n{url}\n建议添加到浏览器收藏夹或桌面快捷方式'
        elif match_num == 16:  # SL
            match = re.match(r'^(?:SL|sl) *([\?？])? *(?:\[CQ:at,qq=(\d+)\])? *([\?？])? *$', cmd)
            if not match:
                return
            behalf = match.group(2) and int(match.group(2))
            only_check = bool(match.group(1) or match.group(3))
            if behalf:
                user_id = behalf
            if only_check:
                sl_ed = self.save_slot(group_id, user_id, only_check=True)
                if sl_ed:
                    return '今日已使用SL'
                else:
                    return '今日未使用SL'
            else:
                try:
                    self.save_slot(group_id, user_id)
                except ClanBattleError as e:
                    _logger.info('群聊 失败 {} {} {}'.format(
                        user_id, group_id, cmd))
                    return str(e)
                _logger.info('群聊 成功 {} {} {}'.format(user_id, group_id, cmd))
                return '已记录SL'
        elif 20 <= match_num <= 25:
            if len(cmd) != 2:
                return
            beh = '挂树' if match_num == 20 else '预约{}号boss'.format(match_num-20)
            subscribers = self.get_subscribe_list(group_id, match_num-20)
            if not subscribers:
                return '没有人'+beh
            reply = beh+'的成员：\n'
            for m in subscribers:
                reply += '\n'+self._get_nickname_by_qqid(m['qqid'])
                if m.get('message'):
                    reply += '：' + m['message']
            return reply

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'clan/<int:group_id>/'),
            methods=['GET'])
        async def yobot_clan(group_id):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member and user.authority_group >= 10):
                return await render_template('clan/unauthorized.html')
            return await render_template(
                'clan/panel.html',
                is_member=is_member,
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/subscribers/'),
            methods=['GET'])
        async def yobot_clan_subscribers(group_id):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member and user.authority_group >= 10):
                return await render_template('clan/unauthorized.html')
            return await render_template(
                'clan/subscribers.html',
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/api/'),
            methods=['POST'])
        async def yobot_clan_api(group_id):
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return jsonify(
                    code=20,
                    message='Group not exists',
                )
            if 'yobot_user' not in session:
                if not(group.privacy & 0x1):
                    return jsonify(
                        code=10,
                        message='Not logged in',
                    )
                user_id = 0
            else:
                user_id = session['yobot_user']
                user = User.get_by_id(user_id)
                is_member = Clan_member.get_or_none(
                    group_id=group_id, qqid=user_id)
                if (not is_member and user.authority_group >= 10):
                    return jsonify(
                        code=11,
                        message='Insufficient authority',
                    )
            try:
                payload = await request.get_json()
                if payload is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if (user_id != 0) and (payload.get('csrf_token') != session['csrf_token']):
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = payload['action']
                if user_id == 0:
                    # 允许游客查看
                    if action not in ['get_member_list', 'get_challenge']:
                        return jsonify(
                            code=10,
                            message='Not logged in',
                        )
                if action == 'get_member_list':
                    return jsonify(
                        code=0,
                        members=self.get_member_list(group_id),
                    )
                elif action == 'get_data':
                    return jsonify(
                        code=0,
                        groupData={
                            'group_id': group.group_id,
                            'group_name': group.group_name,
                            'game_server': group.game_server,
                            'level_4': group.level_4,
                        },
                        bossData=self._boss_data_dict(group),
                        selfData={
                            'is_admin': (is_member and user.authority_group < 100),
                            'user_id': user_id,
                            'today_sl': is_member and (is_member.last_save_slot == pcr_datetime(group.game_server)[0]),
                        }
                    )
                elif action == 'get_challenge':
                    d, _ = pcr_datetime(group.game_server)
                    report = self.get_report(
                        group_id,
                        None,
                        None,
                        pcr_datetime(group.game_server, payload['ts'])[0],
                    )
                    return jsonify(
                        code=0,
                        challenges=report,
                        today=d,
                    )
                elif action == 'get_user_challenge':
                    report = self.get_report(
                        group_id,
                        None,
                        payload['qqid'],
                        None,
                    )
                    try:
                        visited_user = User.get_by_id(payload['qqid'])
                    except peewee.DoesNotExist:
                        return jsonify(code=20, message='user not found')
                    return jsonify(
                        code=0,
                        challenges=report,
                        game_server=group.game_server,
                        user_info={
                            'qqid': payload['qqid'],
                            'nickname': visited_user.nickname,
                        }
                    )
                elif action == 'update_boss':
                    try:
                        bossData, notice = await asyncio.wait_for(
                            asyncio.shield(self._boss_status[group_id]),
                            timeout=30)
                        return jsonify(
                            code=0,
                            bossData=bossData,
                            notice=notice,
                        )
                    except asyncio.TimeoutError:
                        return jsonify(
                            code=1,
                            message='not changed',
                        )
                elif action == 'addrecord':
                    if payload['defeat']:
                        try:
                            status = self.challenge(group_id,
                                                    user_id,
                                                    True,
                                                    None,
                                                    payload['behalf'],
                                                    extra_msg=payload.get(
                                                        'message'),
                                                    )
                        except ClanBattleError as e:
                            _logger.info('网页 失败 {} {} {}'.format(
                                user_id, group_id, action))
                            return jsonify(
                                code=10,
                                message=str(e),
                            )
                        _logger.info('网页 成功 {} {} {}'.format(
                            user_id, group_id, action))
                        if group.notification & 0x01:
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message=str(status),
                                )
                            )
                        return jsonify(
                            code=0,
                            bossData=self._boss_data_dict(group),
                        )
                    else:
                        try:
                            status = self.challenge(group_id,
                                                    user_id,
                                                    False,
                                                    payload['damage'],
                                                    payload['behalf'],
                                                    extra_msg=payload.get(
                                                        'message'),
                                                    )
                        except ClanBattleError as e:
                            _logger.info('网页 失败 {} {} {}'.format(
                                user_id, group_id, action))
                            return jsonify(
                                code=10,
                                message=str(e),
                            )
                        _logger.info('网页 成功 {} {} {}'.format(
                            user_id, group_id, action))
                        if group.notification & 0x01:
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message=str(status),
                                )
                            )
                        return jsonify(
                            code=0,
                            bossData=self._boss_data_dict(group),
                        )
                elif action == 'undo':
                    try:
                        status = self.undo(
                            group_id, user_id)
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(
                            code=10,
                            message=str(e),
                        )
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if group.notification & 0x02:
                        asyncio.ensure_future(
                            self.api.send_group_msg(
                                group_id=group_id,
                                message=str(status),
                            )
                        )
                    return jsonify(
                        code=0,
                        bossData=self._boss_data_dict(group),
                    )
                elif action == 'apply':
                    try:
                        status = self.apply_for_challenge(
                            group_id, user_id,
                            extra_msg=payload['extra_msg'],
                            appli_type=payload['appli_type'],
                        )
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(
                            code=10,
                            message=str(e),
                        )
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if group.notification & 0x04:
                        asyncio.ensure_future(
                            self.api.send_group_msg(
                                group_id=group_id,
                                message=status.info,
                            )
                        )
                    return jsonify(
                        code=0,
                        bossData=self._boss_data_dict(group),
                    )
                elif action == 'cancelapply':
                    try:
                        status = self.cancel_application(
                            group_id, user_id)
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(
                            code=10,
                            message=str(e),
                        )
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if group.notification & 0x08:
                        asyncio.ensure_future(
                            self.api.send_group_msg(
                                group_id=group_id,
                                message='boss挑战已可申请',
                            )
                        )
                    return jsonify(
                        code=0,
                        bossData=self._boss_data_dict(group),
                    )
                elif action == 'save_slot':
                    todaystatus = payload['today']
                    try:
                        self.save_slot(group_id, user_id,
                                       todaystatus=todaystatus)
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(
                            code=10,
                            message=str(e),
                        )
                    sw = '添加' if todaystatus else '删除'
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if group.notification & 0x200:
                        asyncio.ensure_future(
                            self.api.send_group_msg(
                                group_id=group_id,
                                message=(self._get_nickname_by_qqid(user_id)
                                         + f'已{sw}SL'),
                            )
                        )
                    return jsonify(code=0, notice=f'已{sw}SL')
                elif action == 'get_subscribers':
                    subscribers = self.get_subscribe_list(group_id)
                    return jsonify(
                        code=0,
                        group_name=group.group_name,
                        subscribers=subscribers)
                elif action == 'addsubscribe':
                    boss_num = payload['boss_num']
                    message = payload.get('message')
                    try:
                        self.add_subscribe(
                            group_id,
                            user_id,
                            boss_num,
                            message,
                        )
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(
                            code=10,
                            message=str(e),
                        )
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if boss_num == 0:
                        notice = '挂树成功'
                        if group.notification & 0x10:
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message='{}已挂树'.format(user.nickname),
                                )
                            )
                    else:
                        notice = '预约成功'
                        if group.notification & 0x40:
                            notice_message = '{}已预约{}号boss'.format(
                                user.nickname,
                                boss_num,
                            )
                            if message:
                                notice_message += '\n留言：'+message
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message=notice_message,
                                )
                            )
                    return jsonify(code=0, notice=notice)
                elif action == 'cancelsubscribe':
                    boss_num = payload['boss_num']
                    counts = self.cancel_subscribe(
                        group_id,
                        user_id,
                        boss_num,
                    )
                    if counts == 0:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(code=0, notice=(
                            '没有预约记录' if boss_num else '没有挂树记录'))
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if boss_num == 0:
                        notice = '取消挂树成功'
                        if group.notification & 0x20:
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message='{}已取消挂树'.format(
                                        user.nickname),
                                )
                            )
                    else:
                        notice = '取消预约成功'
                        if group.notification & 0x80:
                            asyncio.ensure_future(
                                self.api.send_group_msg(
                                    group_id=group_id,
                                    message='{}已取消预约{}号boss'.format(
                                        user.nickname,
                                        boss_num),
                                )
                            )
                    return jsonify(code=0, notice=notice)
                elif action == 'modify':
                    if user.authority_group >= 100:
                        return jsonify(code=11, message='Insufficient authority')
                    try:
                        status = self.modify(
                            group_id,
                            cycle=payload['cycle'],
                            boss_num=payload['boss_num'],
                            boss_health=payload['health'],
                        )
                    except ClanBattleError as e:
                        _logger.info('网页 失败 {} {} {}'.format(
                            user_id, group_id, action))
                        return jsonify(code=10, message=str(e))
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    if group.notification & 0x100:
                        asyncio.ensure_future(
                            self.api.send_group_msg(
                                group_id=group_id,
                                message=str(status),
                            )
                        )
                    return jsonify(
                        code=0,
                        bossData=self._boss_data_dict(group),
                    )
                elif action == 'send_remind':
                    if user.authority_group >= 100:
                        return jsonify(code=11, message='Insufficient authority')
                    sender = user_id
                    private = payload.get('send_private_msg', False)
                    if private and not self.setting['allow_bulk_private']:
                        return jsonify(
                            code=12,
                            message='私聊通知已禁用',
                        )
                    self.send_remind(group_id,
                                     payload['memberlist'],
                                     sender=sender,
                                     send_private_msg=private)
                    return jsonify(
                        code=0,
                        notice='发送成功',
                    )
                elif action == 'drop_member':
                    if user.authority_group >= 100:
                        return jsonify(code=11, message='Insufficient authority')
                    count = self.drop_member(group_id, payload['memberlist'])
                    return jsonify(
                        code=0,
                        notice=f'已删除{count}条记录',
                    )
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                _logger.error(e)
                return jsonify(code=31, message='missing key: '+str(e))
            except asyncio.CancelledError:
                pass
            except Exception as e:
                _logger.exception(e)
                return jsonify(code=40, message='server error')

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/my/'),
            methods=['GET'])
        async def yobot_clan_user_auto(group_id):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            return redirect(url_for(
                'yobot_clan_user',
                group_id=group_id,
                qqid=session['yobot_user'],
            ))

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/<int:qqid>/'),
            methods=['GET'])
        async def yobot_clan_user(group_id, qqid):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member and user.authority_group >= 10):
                return await render_template('clan/unauthorized.html')
            return await render_template(
                'clan/user.html',
                qqid=qqid,
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/setting/'),
            methods=['GET'])
        async def yobot_clan_setting(group_id):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member):
                return await render_template(
                    'unauthorized.html',
                    limit='本公会成员',
                    uath='无')
            if (user.authority_group >= 100):
                return await render_template(
                    'unauthorized.html',
                    limit='公会战管理员',
                    uath='成员')
            return await render_template('clan/setting.html')

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/setting/api/'),
            methods=['POST'])
        async def yobot_clan_setting_api(group_id):
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user_id = session['yobot_user']
            user = User.get_by_id(user_id)
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return jsonify(
                    code=20,
                    message='Group not exists',
                )
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (user.authority_group >= 100 or not is_member):
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            try:
                payload = await request.get_json()
                if payload is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if payload.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = payload['action']
                if action == 'get_setting':
                    return jsonify(
                        code=0,
                        groupData={
                            'group_name': group.group_name,
                            'game_server': group.game_server,
                            'battle_id': group.battle_id,
                        },
                        privacy=group.privacy,
                        notification=group.notification,
                    )
                elif action == 'put_setting':
                    group.game_server = payload['game_server']
                    group.notification = payload['notification']
                    group.privacy = payload['privacy']
                    group.save()
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    return jsonify(code=0, message='success')
                elif action == 'get_data_slot_record_count':
                    counts = self.get_data_slot_record_count(group_id)
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    return jsonify(code=0, message='success', counts=counts)
                # elif action == 'new_data_slot':
                #     self.new_data_slot(group_id)
                #     _logger.info('网页 成功 {} {} {}'.format(
                #         user_id, group_id, action))
                #     return jsonify(code=0, message='success')
                elif action == 'clear_data_slot':
                    battle_id = payload.get('battle_id')
                    self.clear_data_slot(group_id, battle_id)
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    return jsonify(code=0, message='success')
                elif action == 'switch_data_slot':
                    battle_id = payload['battle_id']
                    self.switch_data_slot(group_id, battle_id)
                    _logger.info('网页 成功 {} {} {}'.format(
                        user_id, group_id, action))
                    return jsonify(code=0, message='success')
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                _logger.error(e)
                return jsonify(code=31, message='missing key: '+str(e))
            except Exception as e:
                _logger.exception(e)
                return jsonify(code=40, message='server error')

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/statistics/'),
            methods=['GET'])
        async def yobot_clan_statistics(group_id):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member and user.authority_group >= 10):
                return await render_template('clan/unauthorized.html')
            return await render_template(
                'clan/statistics.html',
                allow_api=(group.privacy & 0x2),
                apikey=group.apikey,
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/statistics/<int:sid>/'),
            methods=['GET'])
        async def yobot_clan_boss(group_id, sid):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            is_member = Clan_member.get_or_none(
                group_id=group_id, qqid=session['yobot_user'])
            if (not is_member and user.authority_group >= 10):
                return await render_template('clan/unauthorized.html')
            return await render_template(
                f'clan/statistics/statistics{sid}.html',
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/statistics/api/'),
            methods=['GET'])
        async def yobot_clan_statistics_api(group_id):
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return jsonify(code=20, message='Group not exists')
            apikey = request.args.get('apikey')
            if apikey:
                # 通过 apikey 外部访问
                if not (group.privacy & 0x2):
                    return jsonify(code=11, message='api not allowed')
                if apikey != group.apikey:
                    return jsonify(code=12, message='Invalid apikey')
            else:
                # 内部直接访问
                if 'yobot_user' not in session:
                    return jsonify(code=10, message='Not logged in')
                user = User.get_by_id(session['yobot_user'])
                is_member = Clan_member.get_or_none(
                    group_id=group_id, qqid=session['yobot_user'])
                if (not is_member and user.authority_group >= 10):
                    return jsonify(code=11, message='Insufficient authority')
            battle_id = request.args.get('battle_id')
            if battle_id is None:
                pass
            else:
                if battle_id.isdigit():
                    battle_id = int(battle_id)
                elif battle_id == 'all':
                    pass
                elif battle_id == 'current':
                    battle_id = None
                else:
                    return jsonify(code=20, message=f'unexceptd value "{battle_id}" for battle_id')
            # start = int(request.args.get('start')) if request.args.get('start') else None
            # end = int(request.args.get('end')) if request.args.get('end') else None
            # report = self.get_report(group_id, None, None, start, end)
            report = self.get_report(group_id, battle_id, None, None)
            # member_list = self.get_member_list(group_id)
            member_list = self.get_battle_member_list(group_id, battle_id)
            groupinfo = {
                'group_id': group.group_id,
                'group_name': group.group_name,
                'game_server': group.game_server,
                'battle_id': group.battle_id,
            },
            response = await make_response(jsonify(
                code=0,
                message='OK',
                api_version=1,
                challenges=report,
                groupinfo=groupinfo,
                members=member_list,
            ))
            if (group.privacy & 0x2):
                response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'clan/<int:group_id>/progress/'),
            methods=['GET'])
        async def yobot_clan_progress(group_id):
            group = Clan_group.get_or_none(group_id=group_id)
            if group is None:
                return await render_template('404.html', item='公会'), 404
            if not(group.privacy & 0x1):
                if 'yobot_user' not in session:
                    return redirect(url_for('yobot_login', callback=request.path))
                user = User.get_by_id(session['yobot_user'])
                is_member = Clan_member.get_or_none(
                    group_id=group_id, qqid=session['yobot_user'])
                if (not is_member and user.authority_group >= 10):
                    return await render_template('clan/unauthorized.html')
            return await render_template(
                'clan/progress.html',
            )
