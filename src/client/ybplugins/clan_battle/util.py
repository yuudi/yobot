import datetime
import time
from functools import lru_cache
from typing import Tuple, Union

from expiringdict import ExpiringDict

from .typing import Pcr_date, Pcr_time

pcr_time_offset = {
    "jp": 4,
    "tw": 3,
    "kr": 4,
    "cn": 3,
}


@lru_cache(4)
def pcr_tzinfo(area):
    return datetime.timezone(datetime.timedelta(hours=pcr_time_offset[area]))


def pcr_datetime(area, dt: Union[int, datetime.datetime, None] = None) -> Tuple[Pcr_date, Pcr_time]:
    if dt is None:
        ts = int(time.time())
    elif isinstance(dt, int):
        ts = dt
    elif isinstance(dt, datetime.datetime):
        ts = dt.timestamp()
    else:
        raise ValueError(f'cannot parse {type(dt)} to pcrdatetime')
    ts += pcr_time_offset[area]*3600
    return divmod(ts, 86400)


def pcr_timestamp(d: Pcr_date, t: Pcr_time, area) -> int:
    return 86400*d + t - (pcr_time_offset[area]*3600)


def atqq(qqid):
    return '[CQ:at,qq={}]'.format(qqid)


def timed_cached_func(max_len, max_age_seconds, ignore_self=False):
    cache = ExpiringDict(max_len, max_age_seconds)

    def decorator(fn):
        def wrapper(*args, nocache=False):  # args must be hashable
            if ignore_self:
                key = tuple(args[1:])
            else:
                key = tuple(args)
            value = cache.get(key)
            if nocache or value is None:
                value = fn(*args)
                cache[key] = value
            return value
        return wrapper
    return decorator
