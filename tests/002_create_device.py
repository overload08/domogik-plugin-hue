#!/usr/bin/python
#-*- coding: utf-8 -*-create_device.py

### configuration ######################################
DEVICE_NAME_MIRROR = "test_hue"
ADDRESS = "hue"


from domogik.tests.common.testdevice import TestDevice
from domogik.common.utils import get_sanitized_hostname

plugin = 'hue'

def create_device():
    ### create the device, and if ok, get its id in device_id
    client_id  = "plugin-{0}.{1}".format(plugin, get_sanitized_hostname())
    print "Creating the Hue device..."
    td = TestDevice()
    params = td.get_params(client_id, "hue.hue")
        # fill in the params
    params["device_type"] = "hue"
    params["name"] = DEVICE_NAME_MIRROR
    params["address"] = ADDRESS
    for idx, val in enumerate(params['global']):
        if params['global'][idx]['key'] == 'name' :  params['global'][idx]['value'] = NAME
        if params['global'][idx]['key'] == 'address' :  params['global'][idx]['value'] = ADDRESS

    # go and create
    td.create_device(params)
    print "Device Hue {0} configured".format(DEVICE_NAME_KAROTZ)

    
if __name__ == "__main__":
    create_device()
