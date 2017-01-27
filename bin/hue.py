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
@copyright: (C) 2007-2017 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading
import traceback
from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage
from phue import Bridge
import time
import os
import pprint

class HueManager(Plugin):

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='hue')
        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return
        if not os.path.exists(str(self.get_data_files_directory())):
            self.log.info(u"Directory data not exist, trying create : %s", str(self.get_data_files_directory()))
            try:
                os.mkdir(str(self.get_data_files_directory()))
                self.log.info(u"Hue data directory created : %s" % str(self.get_data_files_directory()))
            except Exception as exc:
                self.log.error(exc.message)
        if not os.access(str(self.get_data_files_directory()), os.W_OK):
            self.log.error("No write access on data directory : %s" % (str(self.get_data_files_directory())))
        self.devices = self.get_device_list(quit_if_no_device=True)
        self.commands = self.get_commands(self.devices)
        self.sensors = self.get_sensors(self.devices)
        self.sensors_values = {}
        self.ip_bridge = self.get_config("ip_bridge")
        self.log.info(u"==> commands:   %s" % format(self.commands))
        self.log.info(u"==> sensors:   %s" % format(self.sensors))
        try:
            self.bridge = Bridge(ip=self.ip_bridge, config_file_path=self.get_data_files_directory() + "/bridge.config")
            self.bridge.connect()
        except:
            self.log.error(traceback.format_exc())
            self.force_leave()
        self.device_list = {}
        for a_device in self.devices:
            device_name = a_device["name"]
            device_id = a_device["id"]
            lamp_id = int(self.get_parameter(a_device, "Device"))
            self.device_list.update({device_id : {'name': device_name, 'address': lamp_id}})
            self.launch_thread(a_device)
        self.register_cb_update_devices(self.launch_thread)
        self.ready()

    @staticmethod
    def from_dt_switch_to_off_on(value):
        # 0 - 1 translated to off / on
        if str(value) == "0":
            return False
        else:
            return True

    @staticmethod
    def from_off_on_to_dt_switch(value):
        # off - on translated to 0 - 1
        if value == False:
            return 0
        else:
            return 1

    def launch_thread(self, a_device):
        huethreads = {}
        lamp_id = int(self.get_parameter(a_device, "Device"))
        thr_name = "dev_" + str(a_device["id"])
        huethreads[thr_name] = threading.Thread(None, self.get_status, thr_name, (a_device["id"], lamp_id, self.ip_bridge), {})
        self.log.info(u"Starting thread" + thr_name + " with paramerters : device_id=" + str(a_device["id"]) +", lamp_id=" + str(lamp_id) + ", ip_bridge=" + self.ip_bridge)
        huethreads[thr_name].start()
        self.register_thread(huethreads[thr_name])


    def get_status(self, device_id, lamp_id, bridge_ip):
        old_data = {}
        interval = 300
        previous_time = time.time()
        while not self._stop.isSet():
            data = {}
            try:
                status = self.bridge.get_light(lamp_id, 'on')
                brightness = int(float(self.bridge.get_light(lamp_id, 'bri')/254.00*100.00))
                reachable = self.bridge.get_light(lamp_id, 'reachable')
            except:
                self.log.debug(u"Unable to get device information for id " + str(device_id))
            data[self.sensors[device_id]['light']] = self.from_off_on_to_dt_switch(status)
            self.sensors_values[self.sensors[device_id]['light']] = self.from_off_on_to_dt_switch(status)
            if self.from_off_on_to_dt_switch(status) == 0 or self.from_off_on_to_dt_switch(reachable) == 0:
                data[self.sensors[device_id]['brightness']] = 0
                self.sensors_values[self.sensors[device_id]['brightness']] = 0
            else:
                data[self.sensors[device_id]['brightness']] = brightness
                self.sensors_values[self.sensors[device_id]['brightness']] = brightness
            data[self.sensors[device_id]['reachable']] = self.from_off_on_to_dt_switch(reachable)
            self.sensors_values[self.sensors[device_id]['reachable']] = self.from_off_on_to_dt_switch(reachable)
            try:
                if (data != old_data) or (time.time() - previous_time >= interval):
                    self.log.info(u"==> Lamp '%s' state '%s', brightness '%s', reachable '%s'" % (lamp_id, status, brightness, reachable))
                    self.log.debug(u"Trying to send data sensor...")
                    self._pub.send_event('client.sensor', data)
                    self.log.debug(u"Data sent!")
                    old_data = data
                    previous_time = time.time()
            except:
                # We ignore the message if some values are not correct
                self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
            self._stop.wait(1)

    def on_mdp_request(self, msg):
        self.log.error(u"Received MQ command, processing...")
        Plugin.on_mdp_request(self, msg)
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
                self.send_rep_ack(status, reason, command_id, "unknown")                      # Reply MQ REP (acq) to REQ command
                return
            device_name = self.device_list[device_id]["name"]
            self.log.debug(u"==> Received MQ REQ command message: %s" % format(data))
            command = list(self.commands[device_id].keys())[list(self.commands[device_id].values()).index(command_id)]
            bridgecmd = {}
            if command == "set_brightness":
                new_value = int(float(data['bri'])) * 254/100
                if self.sensors_values[self.sensors[device_id]['light']] == 0:
                    sensors[self.sensors[device_id]['light']] = 1
                    bridgecmd = {'on' : True, 'bri' : new_value}
                else:
                    bridgecmd = {'bri' : new_value}
                sensors[self.sensors[device_id]['brightness']] = data['bri']
                try:
                    self._pub.send_event('client.sensor', sensors)
                except:
                    # We ignore the message if some values are not correct
                    self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))

                self.log.debug(u"Set brightness to '%s' light to '%s'" % (data['bri'], new_value))
                set = self.bridge.set_light(self.device_list[device_id]['address'], bridgecmd)
                if "success" in set:
                    if set.index("success") != -1:
                        status = True
                    else:
                        status = False
            elif command == "set_on":
                sensors[self.sensors[device_id]['light']] = data['switch']
                if data['switch'] == 0:
                    sensors[self.sensors[device_id]['brightness']] = 0
                try:
                    self._pub.send_event('client.sensor', sensors)
                except:
                    # We ignore the message if some values are not correct
                    self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
                set = self.bridge.set_light(self.device_list[device_id]['address'], 'on', self.from_dt_switch_to_off_on(sensors[self.sensors[device_id]['light']]))
                if "success" in set:
                    if set.index("success") != -1:
                        status = True
                    else:
                        status = False
            elif command == "send_alert":
                self.log.debug(u"Sending alert on device %s" % str(self.device_list[device_id]['address']))
                set = self.bridge.set_light(self.device_list[device_id]['address'], 'alert', 'lselect')
                if "success" in set:
                    if set.index("success") != -1:
                        status = True
                    else:
                        status = False

            # Reply MQ REP (acq) to REQ command
            self.send_rep_ack(status, reason, command_id, device_name)
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
    HueManager()
