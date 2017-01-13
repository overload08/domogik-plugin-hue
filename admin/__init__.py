# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail
from jinja2 import TemplateNotFound
from phue import Bridge

### package specific imports
import subprocess



### package specific functions
def list_lights():
    b=Bridge(self.get_config("ip_bridge"))
    b.connect()
    output = b.get_light()
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output


### common tasks
package = "plugin_hue"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)

plugin_hue_adm = Blueprint(package, __name__,
                        template_folder = template_dir,
                        static_folder = static_dir)


@plugin_hue_adm.route('/<client_id>')
def index(client_id):
    detail = get_client_detail(client_id)
    try:
        return render_template('plugin_hue.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced')
    except TemplateNotFound:
        abort(404)

