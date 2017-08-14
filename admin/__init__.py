# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort, request
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail
from jinja2 import TemplateNotFound
from phue import Bridge
from domogik.common.utils import get_sanitized_hostname
import zmq
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
import json
import traceback

### package specific imports
import subprocess



### package specific functions
def list_lights(ip):
    output = ""
    try:
        b=Bridge(ip=ip, config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
        b.connect()
        lights = b.get_light()
        for light in lights:
            output += "Light ID : " + light[0] + "\n"
            output += "    Name : " + lights[light]["name"] + "\n"
            output += "\n"
	output += "-------------------------------------------------------------\n"
	groups = b.get_group()
	for group in groups:
	    lights_group = b.get_group(int(group), 'lights')
	    output += "Group ID : " + group[0] + "\n"
	    output += "    Name : " + groups[group]["name"] + "\n"
	    for light_group in lights_group:
	        output += "        Lamp ID " + light_group[0] + " (" + lights[light_group[0]]["name"] + ")\n"
    except:
	output = "Error while retrieving Hue lamps... Have you push the bridge button?\nRaw output: "
    return output

def select_lights(ip):
    models = {'LCT001':'Hue bulb A19','LCT007':'Hue bulb A19','LCT010':'Hue bulb A19','LCT014':'Hue bulb A19','LCT002':'Hue Spot BR30','LCT003':'Hue Spot GU10','LCT011':'Hue BR30 Richer Colors','LTW011':'Hue BR30 White Ambience','LST001':'Hue LightStrips','LLC010':'Hue Living Colors Iris','LLC011':'Hue Living Colors Bloom','LLC012':'Hue Living Colors Bloom','LLC006':'Living Colors Gen3 Iris','LLC005':'Living Colors Gen3 Bloom, Aura','LLC007':'Living Colors Gen3 Bloom, Aura','LLC014':'Living Colors Gen3 Bloom, Aura','LLC013':'Disney Living Colors','LWB004':'Hue White','LWB006':'Hue White','LWB007':'Hue White','LWB010':'Hue White lamp','LWB014':'Hue White lamp','LLM001':'Color Light Module','LLM010':'Color Temperature Module','LLM011':'Color Temperature Module','LLM012':'Color Temperature Module','LTW001':'Hue A19 White Ambiance','LTW004':'Hue A19 White Ambiance','LTW010':'Hue A19 White Ambiance','LTW015':'Hue A19 White Ambiance','LTW013':'Hue ambiance spot','LLC020':'Hue Go','LST002':'Hue LightStrips Plus','LCT012':'Hue color candle','LTW012':'Hue ambiance candle'}
    output = "<form method=\"POST\" action=\"/plugin_hue/plugin-hue." + get_sanitized_hostname() + "/wizard/create\">"
    try:
        b=Bridge(ip=ip, config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
        b.connect()
        lights = b.get_light()
	output += "<div style=\"margin-left:20px;\">"
	output += "<h3>Lampes</h3>"
	output += "<div style=\"margin-left:20px;\">"
        for light in lights:
	    detail = b.get_light(int(light))
	    output += "<input type=\"checkbox\" name=\"light-" + lights[light]["name"] + "-" + detail["modelid"] + "-" + light[0] + "\">" + " - <input type=\"text\" value=\"" + lights[light]["name"] + "\"> - " + models[detail["modelid"]]  + " - " +"<input type=\"button\" value=\"Test\" onclick=\"testlight(" + light[0] + ")\"><br>"
	output += "</div>"
        groups = b.get_group()
	output += "<h3>Groupes</h3>"
	output += "<div style=\"margin-left:20px;\">"
        for group in groups:
            output += "<input type=\"checkbox\" name=\"group-" + groups[group]["name"] + "-" + group[0] + "\">" + " - <input type=\"text\" value=\"" + groups[group]["name"] + "\"> - <input type=\"button\" value=\"Test\" onclick=\"testgroup(" + group[0] + ")\"><br>"
	output += "</div>"
	output += "</div>"
        output += "<input type=\"hidden\" name=\"bridge\" value=\"" + ip + "\">"
    except:
        output = "Error while retrieving Hue lamps... Have you push the bridge button?"
    return output

def create_device(name, light_id, type):
    try:
        client_id  = "plugin-hue.{0}".format(get_sanitized_hostname())
        devicedata = {'data':
            {
                u'name': name,
                u'description': "",
                u'reference': "",
                u'global': [
                    {
                        u'key': u'Device',
                        u'value': light_id,
                        u'type': u'integer',
                        u'description': ""
                    }
                ],
                u'client_id': client_id,
                u'device_type': type,
                u'xpl': [],
                u'xpl_commands': {},
                u'xpl_stats': {}
            }
        }
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data(devicedata)
        response = cli.request('admin', msg.get(), timeout=10).get()
        create_result = json.loads(response[1])             # response[1] is a string !
        return response
        if not create_result["status"]:
            output = "### Failed to create device"
	else:
	    output = "==> Success to create device"

    except Exception:
        return "ERROR (fct.create_device)==============================<br>" + output + "<br>" + traceback.format_exc() + "<br>END ERROR ====================================<br>"

### common tasks
package = "plugin_hue"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)

plugin_hue_adm = Blueprint(package, __name__,
                        template_folder = template_dir,
                        static_folder = static_dir)

@plugin_hue_adm.route('/<client_id>/wizard/create', methods=['POST'])
def create(client_id):
    models = {'LCT001':'hue.white','LCT007':'hue.white','LCT010':'hue.white','LCT014':'hue.white','LCT002':'hue.white','LCT003':'hue.white','LCT011':'hue.go','LTW011':'hue.white','LST001':'hue.go','LLC010':'hue.go','LLC011':'hue.go','LLC012':'hue.go','LLC006':'hue.go','LLC005':'hue.go','LLC007':'hue.go','LLC014':'hue.go','LLC013':'hue.go','LWB004':'hue.white','LWB006':'hue.white','LWB007':'hue.white','LWB010':'hue.white','LWB014':'hue.white','LLM001':'hue.white','LLM010':'hue.go','LLM011':'hue.go','LLM012':'hue.go','LTW001':'hue.white','LTW004':'hue.white','LTW010':'hue.white','LTW015':'hue.white','LTW013':'hue.white','LLC020':'hue.go','LST002':'hue.go','LCT012':'hue.go','LTW012':'hue.white'}
    dict = request.form
    str_json = json.dumps(dict)

    for key in dict:
        if "bridge" in key:
            bridge_ip = dict[key]
    output = "Connexion au bridge...<br>"
    b=Bridge(ip=bridge_ip, config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
    b.connect()

    output += "Configuration de l'IP du Bridge : " + bridge_ip + "<br>"
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('config.set')
    msg.add_data('type', 'plugin')
    msg.add_data('host', get_sanitized_hostname())
    msg.add_data('name', 'hue')
    msg.add_data('data', {"ip_bridge" : bridge_ip})
    cli.request('admin', msg.get(), timeout=10).get()

    for key in dict:
	if "light" in key:
	    light_id = key.split("-")
    	    output += "Creating device for lamp ID " + light_id[3] + " with name " + light_id[1] + " and type " + str(models[light_id[2]]) + "<br>"
	    try:
                create_device(light_id[1], light_id[3], models[light_id[2]])
            except Exception:
                return "ERROR (create_device.light)===================<br>" + output + "<br>" + traceback.format_exc() + "<br>END ERROR ====================================<br>"

	if "group" in key:
	    group_id = key.split("-")
	    output += "Creating device for group ID " + group_id[2] + " with name " + group_id[1] + "<br>"
	    try:
		create_device(group_id[1], group_id[2], "hue.group")
            except Exception:
                return "ERROR (create_device.group)===================<br>" + output + "<br>" + traceback.format_exc() + "<br>END ERROR ====================================<br>"

    try:
        output += "Arret du plugin...<br>"
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.stop.do')
        msg.add_data('name', 'hue')
        msg.add_data('host', get_sanitized_hostname())
        msg.add_data('type', 'plugin')
        cli.request('manager', msg.get(), timeout=10).get()

    except Exception:
	output += traceback.format_exc() + "<br>"

    try:
        output += "Demarrage du plugin...<br>"
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.start.do')
        msg.add_data('name', 'hue')
        msg.add_data('host', get_sanitized_hostname())
        msg.add_data('type', 'plugin')
        cli.request('manager', msg.get(), timeout=10).get()

    except Exception:
        output += traceback.format_exc() + "<br>"

    detail = get_client_detail(client_id)
    try:
        return render_template('wizard3.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
            hue = output)

    except TemplateNotFound:
        abort(404)

    return output

@plugin_hue_adm.route('/<client_id>/wizard/<bridge_ip>/test/<light_id>')
def test_light(client_id,bridge_ip,light_id):
    try:
        b=Bridge(ip=bridge_ip, config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
	b.connect()
	b.set_light(int(light_id), 'alert', 'select')
        output = "OK"
    except:
        output = "NOK"
    return output

@plugin_hue_adm.route('/<client_id>/wizard/<bridge_ip>')
def wizard2(client_id,bridge_ip):
    detail = get_client_detail(client_id)
    try:
        return render_template('wizard2.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
            hue = select_lights(bridge_ip))

    except TemplateNotFound:
        abort(404)

@plugin_hue_adm.route('/<client_id>/wizard')
def wizard(client_id):
    detail = get_client_detail(client_id)
    import ssdp
    if not detail['data']['configuration'][1]['value']:
        try:
            bridge = ssdp.discover()
        except:
	    bridge = "Aucun bridge trouve"
    else:
	bridge = detail['data']['configuration'][1]['value']
    try:
        return render_template('wizard.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
	    bridge = bridge)

    except TemplateNotFound:
        abort(404)


@plugin_hue_adm.route('/<client_id>')
def index(client_id):
    detail = get_client_detail(client_id)
    try:
        return render_template('plugin_hue.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
	    hue = list_lights(detail['data']['configuration'][1]['value']))

    except TemplateNotFound:
        abort(404)

