from peewee import *
from playhouse.migrate import SqliteMigrator, migrate

from .web_util import rand_string

_db = SqliteDatabase(None)
_version = 3  # 目前版本


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

    privacy = IntegerField(default=3)   # 密码输入错误次数
    clan_group_id = BigIntegerField(null=True)
    last_login_time = BigIntegerField(default=0)
    last_login_ipaddr = IPField(default='0.0.0.0')
    password = FixedCharField(max_length=64, null=True)
    login_code = FixedCharField(max_length=6, null=True)
    login_code_available = BooleanField(default=False)
    login_code_expire_time = BigIntegerField(default=0)
    salt = CharField(max_length=16, default=rand_string)


class User_login(_BaseModel):
    qqid = BigIntegerField()
    auth_cookie = FixedCharField(max_length=64)
    auth_cookie_expire_time = BigIntegerField(default=0)
    last_login_time = BigIntegerField(default=0)
    last_login_ipaddr = IPField(default='0.0.0.0')

    class Meta:
        primary_key = CompositeKey('qqid', 'auth_cookie')


class Clan_group(_BaseModel):
    group_id = BigIntegerField(primary_key=True)
    group_name = TextField(null=True)
    privacy = IntegerField(default=2)
    game_server = CharField(max_length=2, default='cn')
    notification = IntegerField(default=0xffff)  # 需要接收的通知
    level_4 = BooleanField(default=False)  # 公会战是否存在4阶段
    boss_cycle = SmallIntegerField(default=1)
    boss_num = SmallIntegerField(default=1)
    boss_health = BigIntegerField(default=6000000)
    challenging_member_qq_id = IntegerField(null=True)
    boss_lock_type = IntegerField(default=0)  # 1出刀中，2其他
    challenging_start_time = BigIntegerField(default=0)
    challenging_comment = TextField(null=True)


class Clan_member(_BaseModel):
    group_id = BigIntegerField()
    qqid = BigIntegerField()
    role = IntegerField(default=100)
    last_save_slot = IntegerField(null=True)
    remaining_status = TextField(null=True)

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
    message = TextField(null=True)
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


class DB_schema(_BaseModel):
    key = CharField(max_length=64, primary_key=True)
    value = TextField()


def init(sqlite_filename):
    _db.init(
        database=sqlite_filename,
        pragmas={
            'journal_mode': 'wal',
            'cache_size': -1024 * 64,
        },
    )

    old_version = 1
    if not DB_schema.table_exists():
        DB_schema.create_table()
        DB_schema.create(key='version', value=str(_version))
    else:
        old_version = int(DB_schema.get(key='version').value)

    if not User.table_exists():
        Admin_key.create_table()
        User.create_table()
        User_login.create_table()
        Clan_group.create_table()
        Clan_member.create_table()
        Clan_challenge.create_table()
        Clan_subscribe.create_table()
        Character.create_table()
        User_box.create_table()
        old_version = _version
    if old_version > _version:
        print('数据库版本高于程序版本，请升级yobot')
        raise SystemExit()
    if old_version < _version:
        db_upgrade(old_version)


def db_upgrade(old_version):
    migrator = SqliteMigrator(_db)
    if old_version < 2:
        User_login.create_table()
        migrate(
            migrator.add_column('clan_member', 'remaining_status',
                                TextField(null=True)),
            migrator.add_column('clan_challenge', 'message',
                                TextField(null=True)),
            migrator.add_column('clan_group', 'boss_lock_type',
                                IntegerField(default=0)),
            migrator.drop_column('user', 'last_save_slot'),
        )
    if old_version < 3:
        migrate(
            migrator.drop_column('user', 'auth_cookie'),
            migrator.drop_column('user', 'auth_cookie_expire_time'),
        )
    DB_schema.replace(key='version', value=str(_version)).execute()
