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

try:
    import threading
    import traceback


class HueManager(Plugin):

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='hue')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return
        self.managerClients = None
        # get the devices list
        self.refreshDevices()
        # get the config values
        self.managerClients = HueClientsManager(self, self.send_sensor)
        for a_device in self.devices :
            try :
                if self.managerClients.addClient(a_device) :
                    self.log.info(u"Ready to work with device {0}".format(getClientId(a_device)))
                else : self.log.info(u"Device parameters not configured, can't create Hue Client : {0}".format(getClientId(a_device)))
            except:
                self.log.error(traceback.format_exc())
        self.add_stop_cb(self.managerClients.stop)
        self.log.info("Plugin ready :)")
        if self.get_config("send_at_start") : self.managerClients.HueClientsConnection()
        self.ready()

    def __del__(self):
        """Close managerClients"""
        print (u"Try __del__ self.managerClients.")
        del self.managerClients
        self.managerClients = None

    def threadingRefreshDevices(self, max_attempt = 2):
        """Call get_device_list from MQ
            could take long time, run in thread to get free process"""
        threading.Thread(None, self.refreshDevices, "th_refreshDevices", (), {"max_attempt": max_attempt}).start()

    def refreshDevices(self, max_attempt = 2):
        self.devices = self.get_device_list(quit_if_no_device = False, max_attempt = 2)
        if self.devices :
            self.log.debug(u"Device list refreshed: {0}".format(self.devices))
            if self.managerClients is not None : self.managerClients.checkClientsRegistered(self.devices)
        elif self.devices == [] :
            self.log.warning(u"No existing device, create one with admin.")
        else :
            self.log.error(u"Can't retrieve the device list, MQ no response, try again or restart plugin.")

    def _getDmgDevice(self, to):
        """Return the domogik device if there is a correspondence with <to< param, else None.
        """
        self.log.debug(u"Search dmg device for : {0}".format(to))
        dmgDevices = []
        for dmgDevice in self.devices :
            if 'to' in dmgDevice['parameters']:
                if dmgDevice['parameters']['to']['value'] == to :
                    dmgDevices.append(dmgDevice)
        if dmgDevices :
            self.log.debug(u"--- devices find for {0} : {1}".format(to, dmgDevices))
            return dmgDevices
        return []

    def on_message(self, msgid, content):
        """Handle pub message from MQ"""
        if msgid == "device.update":
            self.log.debug(u"New pub message {0}, {1}".format(msgid, content))
            self.threadingRefreshDevices()

    def send_sensor(self, sensor_id, dt_type, value):
        """Send pub message over MQ"""
        self.log.info(u"Sending MQ sensor id:{0}, dt type: {1}, value:{2}" .format(sensor_id, dt_type, value))
        self._pub.send_event('client.sensor',
                         {sensor_id : value})

if __name__ == "__main__":
    HueManager()