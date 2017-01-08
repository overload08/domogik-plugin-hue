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
from domogik.interface.common.interface import Interface
from phue import Bridge


class HueManager(Interface):

    def __init__(self):
        """ Init plugin
        """
        Interface.__init__(self, name='hue')
        if not self.check_configured():
            return
        b = Bridge(self.get_config("ip_bridge"))
        self.ready()

    def process_response(self, response):
        """ Process the butler response
        """

if __name__ == "__main__":
    tts = HueManager()