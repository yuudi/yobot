import os

import jinja2
from quart import session, url_for 

static_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/static'))
template_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/template'))

Ver = 'unknown'


def _vertioned_url_for(endpoint, *args, **kwargs):
    if endpoint == 'yobot_static':
        kwargs['v'] = Ver
    return url_for(endpoint, *args, **kwargs)


_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_folder),
    enable_async=True,
)
_env.globals['session'] = session
_env.globals['url_for'] = _vertioned_url_for


async def render_template(template, **context):
    t = _env.get_template(template)
    return await t.render_async(**context)
