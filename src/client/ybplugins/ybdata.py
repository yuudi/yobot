import random
import string

from peewee import *

_db = SqliteDatabase(None)


def _rand_string(n=16):
    return ''.join(
        random.choice(
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits)
        for _ in range(n)
    )


class _BaseModel(Model):
    class Meta:
        database = _db


class Admin_key(_BaseModel):
    key = TextField(primary_key=True)
    valid = BooleanField()
    key_used = BooleanField()
    cookie = TextField(index=True)
    create_time = TimestampField()


class User(_BaseModel):
    qqid = BigIntegerField(primary_key=True)
    nickname = TextField(null=True)

    # 1:主人 2:机器人管理员 10:公会战管理员 100:成员
    authority_group = IntegerField(default=100)

    privacy = IntegerField(default=3)   # 2:本公会成员 3:所有人
    clan_group_id = BigIntegerField(null=True)
    last_save_slot = IntegerField(null=True)
    last_login_time = BigIntegerField(default=0)
    last_login_ipaddr = IPField(default='0.0.0.0')
    password = FixedCharField(max_length=64, null=True)
    login_code = FixedCharField(max_length=6, null=True)
    login_code_available = BooleanField(default=False)
    login_code_expire_time = BigIntegerField(default=0)
    salt = CharField(max_length=16, default=_rand_string)
    auth_cookie = FixedCharField(max_length=64, null=True)
    auth_cookie_expire_time = BigIntegerField(default=0)


class Clan_group(_BaseModel):
    group_id = BigIntegerField(primary_key=True)
    group_name = TextField(null=True)
    privacy = IntegerField(default=2)  # 2:本公会成员 3:所有人
    game_server = CharField(max_length=2, default='cn')
    notification = IntegerField(default=0xffff)  # 需要接收的通知
    level_4 = BooleanField(default=False)  # 公会战是否存在4阶段
    boss_cycle = SmallIntegerField(default=1)
    boss_num = SmallIntegerField(default=1)
    boss_health = BigIntegerField(default=6000000)
    challenging_member_qq_id = IntegerField(null=True)
    challenging_start_time = BigIntegerField(default=0)
    challenging_comment = TextField(null=True)


class Clan_member(_BaseModel):
    group_id = BigIntegerField()
    qqid = BigIntegerField()
    role = IntegerField(default=100)
    last_save_slot = IntegerField(null=True)

    class Meta:
        primary_key = CompositeKey('group_id', 'qqid')


class Clan_challenge(_BaseModel):
    cid = AutoField(primary_key=True)
    gid = BigIntegerField()
    qqid = BigIntegerField()
    challenge_pcrdate = IntegerField()
    challenge_pcrtime = IntegerField()
    boss_cycle = SmallIntegerField()
    boss_num = SmallIntegerField()
    boss_health_ramain = BigIntegerField()
    challenge_damage = BigIntegerField()
    is_continue = BooleanField()  # 此刀是结余刀
    comment = TextField(null=True)


class Clan_subscribe(_BaseModel):
    sid = AutoField(primary_key=True)
    gid = BigIntegerField()
    qqid = IntegerField()
    subscribe_item = SmallIntegerField()
    comment = TextField(null=True)

    class Meta:
        indexes = (
            (('gid', 'qqid', 'subscribe_item'), False),
        )


class Character(_BaseModel):
    chid = IntegerField(primary_key=True)
    name = CharField(max_length=64)
    frequent = BooleanField(default=True)
    comment = TextField()


class Chara_nickname(_BaseModel):
    name = CharField(max_length=64, primary_key=True)
    chid = IntegerField()


class User_box(_BaseModel):
    qqid = BigIntegerField()
    chid = IntegerField()
    last_use = IntegerField()
    rank = IntegerField()
    stars = IntegerField()
    equit = BooleanField()
    comment = TextField()

    class Meta:
        primary_key = CompositeKey('qqid', 'chid')


def init(sqlite_filename):
    _db.init(
        database=sqlite_filename,
        pragmas={
            'journal_mode': 'wal',
            'cache_size': -1024 * 64,
        },
    )

    if not Admin_key.table_exists():
        Admin_key.create_table()
    if not User.table_exists():
        User.create_table()
    if not Clan_group.table_exists():
        Clan_group.create_table()
    if not Clan_member.table_exists():
        Clan_member.create_table()
    if not Clan_challenge.table_exists():
        Clan_challenge.create_table()
    if not Clan_subscribe.table_exists():
        Clan_subscribe.create_table()
    if not Character.table_exists():
        Character.create_table()
    if not User_box.table_exists():
        User_box.create_table()
