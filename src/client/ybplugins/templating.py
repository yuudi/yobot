import datetime
import os

import jinja2
from quart import url_for

static_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/static'))
template_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/template'))

_tz_beijing = datetime.timezone(datetime.timedelta(hours=8))


def from_timestamp(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp, _tz_beijing)
    return dt.strftime('%Y{}%m{}%d{} %H:%M:%S').format(*'年月日')


_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_folder),
    enable_async=True,
)
_env.globals['url_for'] = url_for
_env.globals['from_timestamp'] = from_timestamp


async def render_template(template, **context):
    t = _env.get_template(template)
    return await t.render_async(**context)
