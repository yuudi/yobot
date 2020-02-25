from peewee import *

_db = None


class basemodel(Model):
    class Meta:
        database = _db


class User(basemodel):
    qqid = BigIntegerField(primary_key=True)
    authority_group = IntegerField(default=100)
    nickname = TextField(null=True)
    clan_group_id = BigIntegerField(null=True)
    last_save_slot = IntegerField(null=True)
    last_login_time = BigIntegerField(default=0)
    last_login_ipaddr = IPField(default='0.0.0.0')
    login_code = FixedCharField(max_length=6, null=True)
    login_code_available = BooleanField(default=False)
    login_code_expire_time = BigIntegerField(default=0)
    auth_cookie = FixedCharField(max_length=32, null=True)
    auth_cookie_expire_time = BigIntegerField(default=0)


class Clan_group(basemodel):
    group_id = BigIntegerField(primary_key=True)
    group_name = TextField(null=True)
    game_server = CharField(max_length=2, default='cn')
    level_4 = BooleanField(default=False)
    boss_cycle = SmallIntegerField(default=1)
    boss_num = SmallIntegerField(default=1)
    boss_health = BigIntegerField(default=6000000)
    challenging_member_qq_id = IntegerField(null=True)
    challenging_start_time = TimestampField(default=0)
    challenging_comment = TextField(null=True)


class Clan_challenge(basemodel):
    cid = AutoField(primary_key=True)
    gid = BigIntegerField()
    qqid = BigIntegerField()
    challenge_pcrdate = IntegerField()
    challenge_pcrtime = IntegerField()
    boss_cycle = SmallIntegerField()
    boss_num = SmallIntegerField()
    boss_health_ramain = BigIntegerField()
    challenge_damage = BigIntegerField()
    is_continue = BooleanField()
    is_canceled = BooleanField(default=False)
    comment = TextField(null=True)


class Clan_subscribe(basemodel):
    sid = AutoField(primary_key=True)
    gid = BigIntegerField()
    qqid = IntegerField()
    subscribe_item = SmallIntegerField()
    comment = TextField(null=True)

    class Meta:
        indexes = (
            (('gid', 'qqid', 'subscribe_item'), False),
        )


class Character(basemodel):
    chid = IntegerField(primary_key=True)
    name = TextField()
    frequent = BooleanField(default=True)


class User_pool(basemodel):
    qqid = BigIntegerField()
    chid = IntegerField()
    last_use = IntegerField()


def init(database):
    global _db
    _db = database
    if not User.table_exists():
        User.create_table()
    if not Clan_group.table_exists():
        Clan_group.create_table()
    if not Clan_challenge.table_exists():
        Clan_challenge.create_table()
    if not Clan_subscribe.table_exists():
        Clan_subscribe.create_table()
    if not Character.table_exists():
        Character.create_table()
    if not User_pool.table_exists():
        User_pool.create_table()
