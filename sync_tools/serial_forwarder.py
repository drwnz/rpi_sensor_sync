#!/usr/bin/env python
#
#  Copyright 2020 The Autoware Foundation. All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ********************
#  v0.1.0: drwnz (david.wong@tier4.jp)
#
#  serial_forwarder.py
#
#  Created on: May 28th 2020
#

import threading
import utils
import serial
import socket

class serial_forward (threading.Thread):

    def __init__(self):
        """
        Run the serial forwarding service (for NMEA sentences).
        Configure input serial with 'configure_serial' and add output sockets with 'add_destination'.
        Then run the thread with start().
        """
        self.input_port = '/dev/ttyS0'
        self.baudrate = 9600
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.bytesize = serial.EIGHTBITS
        self.timeout = 1

        self.destination_sockets = []

        threading.Thread.__init__(self)

    def run(self):
        try:
            serial_input = serial.Serial(
                port = self.input_port,
                baudrate = self.baudrate,
                parity = self.parity,
                stopbits = self.stopbits,
                bytesize = self.bytesize,
                timeout = self.timeout
            )
        except:
            print("Could not open port on {}. Not forwarding serial NMEA messages". format(port))

        while 1:
            nmea_message = serial_input.readline()
            if nmea_message[1 : 6] == "GPGGA" or nmea_message[1 : 6] == "GPRMC":
                for destination_socket in self.destination_sockets:
                    destination_socket.sendall(nmea_message)
            else:
                print("Invalid NMEA message received on serial port")

    def configure_serial(self, port, baudrate, parity, stopbits, bytesize, timeout):
        """
        Configures the input serial.
        """
        self.input_port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout

    def add_destination(self, host, port):
        """
        Adds a destination sensor to forward serial messages to over ethernet.
        The destination host and port are checked for usability.
        """
        destination_socket = None
        if utils.check_ip_port_open(host, port):
            try:
                destination_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                destination_socket.settimeout(1)
                destination_socket.connect((host, port))
                self.destination_sockets.append(destination_socket)
            except:
                print("Could not reach the device on {}:{}. Not forwarding serial NMEA messages". format(host, port))
        else:
            print("Could not reach the device on {}:{}. Is the socket already in use? Not forwarding serial NMEA messages". format(host, port))
