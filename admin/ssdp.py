import socket

# UPnP SSDP Search request header
HEADER = b"""M-SEARCH * HTTP/1.1\r
HOST: 239.255.255.250:1900\r
MAN: "ssdp:discover"\r
ST: ssdp:all\r
MX: 3\r
\r
"""

def discover():
    """ Locate Hue Bridge IP using UPnP SSDP search. Discovery will return
    when bridge is found or 3 seconds after last device response. Returns IP
    address or None."""
    #On ESP8266, disable AP WLAN to force use of STA interface
    #import network
    #ap = network.WLAN(network.AP_IF)
    #ap.active(False)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(HEADER, ('239.255.255.250',1900))    #UPnP Multicast
    s.settimeout(3)

    IP = None
    while IP == None:
        data, addr = s.recvfrom(1024)
        lines = data.split(b'\r\n')
        for l in lines:
           tokens = l.split(b' ')
           if tokens[0] == b'LOCATION:':
                url = tokens[1].split(b'/')
                IP = str(url[2])
                break

    s.close()
    return IP
