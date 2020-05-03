#!/usr/bin/env python

import socket
import operator


## Verifies if the port on the specified ip is available in a non blocking way.
# @param ip the IP of the host to check.
# @param port the port to check
# @return boolean indicating if the port is open
def check_ip_port_open(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect((ip, int(port)))
        sock.shutdown(2)
        return True
    except:
        return False


## Obtains the checksum of an nmea sentence
# @param nmea sentence string
# @return checksum string
def get_nmea_checksum(nmea_sentence):
    checksum = reduce(operator.xor, (ord(c) for c in nmea_sentence), 0)
    return checksum