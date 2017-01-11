#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Control and status for Hue lights

Implements
==========

Philips Hue Manager

@author: OverLoad <y.poilvert@geekinfo.fr>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading
import traceback
from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage
from phue import Bridge
import pprint

class HueManager(Plugin):

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='hue')
	self.devices = self.get_device_list(quit_if_no_device=True)
	self.commands = self.get_commands(self.devices)
	self.sensors = self.get_sensors(self.devices)
	self.log.info(u"==> commands:   %s" % format(self.commands))
	self.log.info(u"==> sensors:   %s" % format(self.sensors))
        b = Bridge(self.get_config("ip_bridge"))
	b.connect()
	data = {}
	self.device_list = {}
	for a_device in self.devices:
	    device_name = a_device["name"]
	    device_id = a_device["id"]
	    sensor_address = self.get_parameter(a_device, "Device")
	    self.device_list.update({device_id : {'name': device_name, 'address': sensor_address}})
	    status = b.get_light(self.device_list[device_id]['address'],'on')
	    brightness = b.get_light(self.device_list[device_id]['address'],'bri')/254*100
	    self.log.info(u"==> Device '%s' (id:%s), Sensor: '%s'" % (device_name, device_id, self.sensors[device_id]))
	    self.log.info(u"==> Device '%s' state '%s', brightness '%s'" % (device_name, status, brightness))
	    data[self.sensors[device_id]['light']] = status
	    data[self.sensors[device_id]['brightness']] = brightness
            try:
                self._pub.send_event('client.sensor', data)
            except:
                # We ignore the message if some values are not correct
                self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                pass
        self.ready()

    def on_mdp_request(self, msg):
	Plugin.on_mdp_request(self, msg)
        b = Bridge(self.get_config("ip_bridge"))
        b.connect()
	sensors = {}
	if msg.get_action() == "client.cmd":
            reason = None
            status = True
            data = msg.get_data()
            device_id = data["device_id"]
            command_id = data["command_id"]
            if device_id not in self.device_list:
                self.log.error(u"### MQ REQ command, Device ID '%s' unknown, Have you restarted the plugin after device creation ?" % device_id)
                status = False
                reason = u"Plugin Hue: Unknown device ID %d" % device_id
                self.send_rep_ack(status, reason, command_id, "unknown") ;                      # Reply MQ REP (acq) to REQ command
                return
	    device_name = self.device_list[device_id]["name"]
	    self.log.debug(u"==> Received MQ REQ command message: %s" % format(data))
	    command = list(self.commands[device_id].keys())[list(self.commands[device_id].values()).index(command_id)]
	    print command
	    if command == "set_brightness":
    	        if data['current'] == '0':
                    sensors[self.sensors[device_id]['light']] = 0
	        else:
		    sensors[self.sensors[device_id]['light']] = 1
                sensors[self.sensors[device_id]['brightness']] = data['current']
                new_value = int(data['current']) * 254/100
                status = b.set_light(self.device_list[device_id]['address'], 'bri', new_value)
	    elif command == "set_on":
                if data['current'] == '0':
		    sensors[self.sensors[device_id]['light']] = 'False'
		else:
		    sensors[self.sensors[device_id]['light']] = 'True'
                sensors[self.sensors[device_id]['brightness']] = data['current']
		status = b.set_light(self.device_list[device_id]['address'], 'on', sensors[self.sensors[device_id]['light']])
            try:
                self._pub.send_event('client.sensor', sensors)
            except:
                # We ignore the message if some values are not correct
                self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                pass
			
	    new_value = int(data['current']) * 254/100	
	    status = b.set_light(self.device_list[device_id]['address'], 'bri', new_value)
            
            # Reply MQ REP (acq) to REQ command
            self.send_rep_ack(status, reason, command_id, device_name) ;
	    return

    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ Send MQ REP (acq) to command
        """
        self.log.info(u"==> Reply MQ REP (acq) to REQ command id '%s' for device '%s'" % (cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())

if __name__ == "__main__":
    tts = HueManager()
