import os

import jinja2
from quart import session, url_for

static_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/static'))
template_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../public/template'))


_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_folder),
    enable_async=True,
)
_env.globals['session'] = session
_env.globals['url_for'] = url_for


async def render_template(template, **context):
    t = _env.get_template(template)
    return await t.render_async(**context)
