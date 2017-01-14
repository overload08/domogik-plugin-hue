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
import time
import os

def from_DT_Switch_to_off_on(x):
    # 0 - 1 translated to off / on
    if str(x) == "0":
        return False
    else:
        return True

def from_off_on_to_DT_Switch(x):
    # off - on translated to 0 - 1
    if x == False:
        return 0
    else:
        return 1

class HueManager(Plugin):

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='hue')
        if not os.path.exists(str(self.get_data_files_directory())):
            self.log.info(u"Directory data not exist, trying create : %s", str(self.get_data_files_directory()))
            try:
                os.mkdir(str(self.get_data_files_directory()))
                self.log.info(u"Hue data directory created : %s" % str(self.get_data_files_directory()))
            except Exception as e:
                self.log.error(e.message)
        if not os.access(str(self.get_data_files_directory()), os.W_OK):
            self.log.error("No write access on data directory : %s" % (str(self.get_data_files_directory())))
	self.devices = self.get_device_list(quit_if_no_device=True)
	self.commands = self.get_commands(self.devices)
	self.sensors = self.get_sensors(self.devices)
	self.log.info(u"==> commands:   %s" % format(self.commands))
	self.log.info(u"==> sensors:   %s" % format(self.sensors))
	try:
            b = Bridge(ip=self.get_config("ip_bridge"),config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
    	    b.connect()
	except:
	    self.log.error(traceback.format_exc())
	    self.force_leave()
	data = {}
	self.device_list = {}
	huethreads = {}
	for a_device in self.devices:
	    device_name = a_device["name"]
	    device_id = a_device["id"]
	    sensor_address = self.get_parameter(a_device, "Device")
	    self.device_list.update({device_id : {'name': device_name, 'address': sensor_address}})
            thr_name = "dev_{0}".format(a_device['id'])
            huethreads[thr_name] = threading.Thread(None,self.get_status,thr_name,(self.log,device_id,sensor_address,self.get_config("ip_bridge")),{})
	    self.log.info(u"Starting thread" + thr_name + " with paramerters : device_id=" + str(device_id) +", sensor_address=" + str(sensor_address) + ", ip_bridge=" + self.get_config("ip_bridge"))
            huethreads[thr_name].start()
            self.register_thread(huethreads[thr_name])
#	self.register_cb_update_devices(myHandleDeviceUpdate)
        self.ready()

#    def myHandleDeviceUpdate(self, devices):
#        for hardDevice in self._myHardDevices:
#            hardDevice.refreshAllDmgDevice(devices)
#        self.log.info(u"All hard devives are updated from domogik devices")

    def get_status(self, log, device_id, address,bridge_ip):
	while not self._stop.isSet():
            b = Bridge(ip=bridge_ip,config_file_path="/var/lib/domogik/domogik_packages/plugin_hue/data/bridge.config")
            b.connect()
	    data = {}
	    status = b.get_light(address,'on')
	    brightness = b.get_light(address,'bri')/254.00*100.00
	    reachable = b.get_light(address,'reachable')
	    self.log.info(u"==> Device '%s' state '%s', brightness '%s', reachable '%s'" % (device_id, status, brightness, reachable))
            data[self.sensors[device_id]['light']] = from_off_on_to_DT_Switch(status)
            data[self.sensors[device_id]['brightness']] = brightness
	    data[self.sensors[device_id]['reachable']] = from_off_on_to_DT_Switch(reachable)
            try:
		self.log.debug(u"Trying to send data sensor...")
                self._pub.send_event('client.sensor', data)
            except:
                # We ignore the message if some values are not correct
                self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                pass
	time.sleep(1)

    def on_mdp_request(self, msg):
	self.log.error(u"Received MQ command, processing...")
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
	    if command == "set_brightness":
    	        if data['current'] == 0:
                    sensors[self.sensors[device_id]['light']] = 0
	        else:
		    sensors[self.sensors[device_id]['light']] = 1
		sensors[self.sensors[device_id]['brightness']] = data['current']
                try:
                    self._pub.send_event('client.sensor', sensors)
                except:
                    # We ignore the message if some values are not correct
                    self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                    pass

                new_value = int(data['current']) * 254/100
		self.log.debug(u"Set brightness to '%s'  light to '%s'" % (data['current'], new_value))
                set = b.set_light(self.device_list[device_id]['address'], 'bri', new_value)
		if ("success" in set):
    		    if (set.index("success")) != -1:
		        status = True
		    else:
		        status = False
	    elif command == "set_on":
	        sensors[self.sensors[device_id]['light']] = data['current']
                try:
                    self._pub.send_event('client.sensor', sensors)
                except:
                    # We ignore the message if some values are not correct
                    self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                    pass
	        set = b.set_light(self.device_list[device_id]['address'], 'on', from_DT_Switch_to_off_on(sensors[self.sensors[device_id]['light']]))	
	        if ("success" in set):
		    if (set.index("success")) != -1:
		        status = True
	            else:
		        status = False
            
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
