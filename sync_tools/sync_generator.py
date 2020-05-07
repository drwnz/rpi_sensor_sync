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
#  sync_generator.py
#
#  Created on: April 19th 2020
#

import pigpio
import utils
import socket
import time

class waveform_engine:

    def __init__(self, pi):
        """
        The frequency output defaults to 1 Hertz for 1PPS, with 20 millisecond on time.
        It will be adjusted to match the input 1PPS where available.
        """
        self.pi = pi

        self.PPS_input_gpio = -1
        self.PPS_input_cycle_time = 0.0           # PPS input cycle time in microseconds, measured
        self.PPS_input_tick = 0
        self.PPS_input_has_ticked = False

        self.PPS_output_gpio = -1
        self.PPS_output_cycle_time = 1000000.0    # PPS output cycle time in microseconds, measured
        self.PPS_output_pulse = 200000.0          # PPS pulse width in microseconds
        self.PPS_output_tick = 0
        self.PPS_output_offset = 0.0              # PPS offset in microseconds
        self.PPS_slack_threshold = 5              # PPS slack limit requiring correction in microseconds
        self.PPS_overtime_reject = 1100000.0      # Reject PPS frequency measurement if it has been too long (GPS lost)


        self.trigger_output_gpio = []
        self.trigger_output_frequency = []
        self.trigger_output_phase = []            # Phase difference from base (PPS) output
        self.trigger_duty_cycle_fraction = 0.5

        self.wave = None
        self.stopped = False

        self.callbacks_set = False
        self.PPS_input_callback = None
        self.PPS_output_callback = None

        self.sensor_port = 10110                    # Default for Velodyne
        self.sensor_IP = None
        self.socket = None
        self.spoof_NMEA = False

    def set_PPS_input_gpio(self, gpio):
        """
        Sets the input PPS GPIO pin.
        If not set, no input PPS will be used.
        """
        self.PPS_input_gpio = gpio
        self.pi.set_mode(gpio, pigpio.INPUT)

    def set_PPS_output_gpio(self, gpio):
        """
        Sets the output PPS GPIO pin.
        If not set, base PPS will be generated but not propagated to output.
        The change takes affect when the update function is called.
        """
        self.PPS_output_gpio = gpio
        self.pi.set_mode(gpio, pigpio.OUTPUT)

    def start_NMEA_spoof(self, port, host):
        """
        Starts the sending of spoof NMEA messages to be sent to a sensor over ethernet.
        Spoof messages will be sent directly after the output PPS rising edges.
        The output PPS signal must be configured for this to operate.
        """
        if self.PPS_output_gpio != -1 and utils.check_ip_port_open(host, port):
            self.sensor_port = port
            self.sensor_IP = host
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(1)
                self.socket.connect((host, port))
                self.spoof_NMEA = True
            except:
                self.spoof_NMEA = False
                print("Could not reach the device on {}:{}. Not spoofing.". format(host, port))
        else:
            print("Output PPS must be configured for NMEA spoofing")

    def stop_NMEA_spoof(self):
        """
        Stops the sending of spoof NMEA messages.
        """
        if self.spoof_NMEA and self.socket is not None:
            self.socket.close()
            if not self.callbacks_set:
                self.PPS_output_callback.cancel()
            self.spoof_NMEA = False

    def set_PPS_output_pulse(self, pulse_time):
        """
        Sets the output PPS pulse width by specifying the pulse time in microseconds.
        The change takes affect when the update function is called.
        """
        self.PPS_output_pulse = pulse_time

    def set_PPS_output_cycle_time(self, cycle_time):
        """
        Sets the output PPS frequency by specifying the cycle time in microseconds.
        The change takes affect when the update function is called.
        """
        self.PPS_output_cycle_time = cycle_time

    def set_PPS_slack_threshold(self, slack_threshold):
        """
        Sets the allowed slack between in the input and output PPS signals in microseconds.
        If the time between rising edges of the waves is less than this number, no further adjustments will be made.
        The change takes affect when the update function is called.
        """
        self.PPS_slack_threshold = slack_threshold

    def set_PPS_overtime_reject_threshold(self, overtime_reject):
        """
        Sets the longest acceptable PPS cycle time to accept as valid input.
        This prevents incorrect PPS frequency measurement when a PPS signal is lost or clock overruns.
        The change takes affect when the update function is called.
        """
        self.PPS_overtime_reject = overtime_reject

    def add_trigger_gpio(self, gpio, frequency = 1, phase = 0):
        """
        Adds an output trigger waveform.
        Frequency must be an integer number.
        Phase must be in degrees.
        The change takes affect when the update function is called.
        """
        gpio_used = False
        for i in range(len(self.trigger_output_gpio)):
            if self.trigger_output_gpio[i] == gpio:
                self.trigger_output_frequency[i] = frequency
                self.trigger_output_phase[i] = phase
                self.pi.set_mode(gpio, pigpio.OUTPUT)
                gpio_used = True

        if not gpio_used:
            self.trigger_output_gpio.append(gpio)
            self.trigger_output_frequency.append(frequency)
            self.trigger_output_phase.append(phase)
            self.pi.set_mode(gpio, pigpio.OUTPUT)

        # Enable usage even without a 1PPS output
        if self.PPS_output_gpio == -1:
            self.PPS_output_cycle_time = 1000000.0
            self.PPS_output_offset = 0.0

    def remove_trigger_gpio(self, gpio):
        """
        Removes an output trigger waveform.
        The change takes affect when the update function is called.
        """
        for i in range(len(self.trigger_output_gpio)):
            if self.trigger_output_gpio[i] == gpio:
                del self.trigger_output_frequency[i]
                del self.trigger_output_phase[i]
                del self.trigger_output_gpio[i]

    def update_trigger_gpio_frequency(self, gpio, frequency):
        """
        Sets the frequency (in Hertz) of an output trigger waveform.
        The output must already exist.
        The change takes affect when the update function is called.
        """
        for i in range(len(self.trigger_output_gpio)):
            if self.trigger_output_gpio[i] == gpio:
                self.trigger_output_frequency[i] = frequency

    def update_trigger_gpio_phase(self, gpio, phase):
        """
        Sets the phase (in degrees) of an output trigger waveform.
        The output must already exist.
        The change takes affect when the update function is called.
        """
        for i in range(len(self.trigger_output_gpio)):
            if self.trigger_output_gpio[i] == gpio:
                self.trigger_output_phase[i] = phase

    def start_PPS_input_sychronization(self):
        """
        Starts synchronization by enabling the callback functions for wave timing.
        """
        if (self.PPS_input_gpio != -1) and not self.callbacks_set:
            self.PPS_input_callback = self.pi.callback(self.PPS_input_gpio, pigpio.RISING_EDGE, self.wave_callback)
            self.PPS_output_callback = self.pi.callback(self.PPS_output_gpio, pigpio.RISING_EDGE, self.wave_callback)
            self.callbacks_set = True
        elif not self.callbacks_set:
            print ("Synchronization to external PPS already running")
        else:
            print ("Input and output PPS must be configured for external synchronization")

    def stop_PPS_input_sychronization(self):
        """
        Stops synchronization by disabling the callback functions for wave timing.
        """
        if self.callbacks_set:
            self.PPS_input_callback.cancel()
            self.PPS_output_callback.cancel()
            self.callbacks_set = False

    def wave_callback(self, gpio, level, tick):
        """
        Callback function for PPS waveform rising edges.
        """
        slack = 0
        if gpio == self.PPS_input_gpio:
            if self.PPS_input_tick > 0:
                time_since_last_tick = tick - self.PPS_input_tick
                if time_since_last_tick < self.PPS_overtime_reject:
                    self.PPS_input_cycle_time = time_since_last_tick
                    self.PPS_output_cycle_time = self.PPS_input_cycle_time
                #print ('Cycle time: %d'%self.PPS_output_cycle_time)
            self.PPS_input_tick = tick
            self.PPS_input_has_ticked = True
            #print('Input: %d'%tick)

        elif gpio == self.PPS_output_gpio:
            self.PPS_output_tick = tick
            #print('Output: %d'%tick)
            if self.PPS_input_has_ticked:
                self.PPS_input_has_ticked = False
                slack = self.PPS_output_tick - self.PPS_input_tick
                #print('Slack: %d'%slack)
                if slack > self.PPS_slack_threshold and slack < (self.PPS_output_cycle_time - self.PPS_slack_threshold):
                    offset = self.PPS_output_offset + slack
                    if offset >= self.PPS_output_cycle_time:
                        offset = offset - self.PPS_output_cycle_time
            	    #print('Offset: %d ... UPDATE'%offset)
                    self.PPS_output_offset = offset
                    self.update()
                else:
                    #print('Offset: %d'%self.PPS_output_offset)
                    pass

            # NMEA spoofing
            if self.spoof_NMEA:
                localticks = time.time() #NOTE: this is only accurate to ~100 micros. Have to fix this later.
                localtime = time.localtime(localticks)
                message = b'$GPGGA,%02d%02d%02d.%03d,4321.428,S,17242.305,E,1,12,1.0,0.0,M,0.0,M,,'%(localtime.tm_hour,localtime.tm_min,localtime.tm_sec, (localticks % 1)*1000)
                checksum = utils.get_nmea_checksum(message)
                nmea_message = message + '*' + checksum + '\r\n'
                self.socket.sendall(nmea_message)

    def update(self):
        """
        Updates the waveform for each GPIO to reflect the current settings.
        """
        if self.PPS_output_pulse > self.PPS_output_cycle_time:
            self.PPS_output_pulse = self.PPS_output_cycle_time

        if self.PPS_output_gpio != -1:
            if self.PPS_output_offset >= self.PPS_output_pulse:
                self.pi.wave_add_generic([
                    pigpio.pulse(0, 1<<self.PPS_output_gpio, self.PPS_output_cycle_time - self.PPS_output_offset),
                    pigpio.pulse(1<<self.PPS_output_gpio, 0, self.PPS_output_pulse),
                    pigpio.pulse(0, 1<<self.PPS_output_gpio, self.PPS_output_offset - self.PPS_output_pulse)
                ])
            else:
                self.pi.wave_add_generic([
                    pigpio.pulse(1<<self.PPS_output_gpio, 0, self.PPS_output_pulse - self.PPS_output_offset),
                    pigpio.pulse(0, 1<<self.PPS_output_gpio, self.PPS_output_cycle_time - self.PPS_output_pulse),
                    pigpio.pulse(1<<self.PPS_output_gpio, 0, self.PPS_output_offset)
                ])

        for gpio, frequency, phase in zip(self.trigger_output_gpio, self.trigger_output_frequency, self.trigger_output_phase):
            trigger_cycle_time = self.PPS_output_cycle_time/frequency
            offset = (self.PPS_output_offset + (self.PPS_output_cycle_time * (360 - phase/frequency) / 360)) % trigger_cycle_time
            on_time = self.trigger_duty_cycle_fraction*trigger_cycle_time
            waves = []
            for i in range(frequency):
                if offset >= on_time:
                    waves.append(pigpio.pulse(0, 1<<gpio, trigger_cycle_time - offset))
                    waves.append(pigpio.pulse(1<<gpio, 0, on_time))
                    waves.append(pigpio.pulse(0, 1<<gpio, offset - on_time))
                else:
                    waves.append(pigpio.pulse(1<<gpio, 0, on_time - offset))
                    waves.append(pigpio.pulse(0, 1<<gpio, trigger_cycle_time - on_time))
                    waves.append(pigpio.pulse(1<<gpio, 0, offset))

            self.pi.wave_add_generic(waves)

        if (len(self.trigger_output_gpio) or (self.PPS_output_gpio != -1)) and not self.stopped:

            new_wave = self.pi.wave_create()

            if self.wave is not None:
                self.pi.wave_send_using_mode(new_wave, pigpio.WAVE_MODE_REPEAT_SYNC)
                while self.pi.wave_tx_at() != new_wave:
                   pass
                self.pi.wave_delete(self.wave)
            else:
                self.pi.wave_send_repeat(new_wave)

            self.wave = new_wave

    def cancel(self):
        """
        Cancels output on the GPIO.
        """
        self.stopped = True
        self.stop_PPS_input_sychronization()
        self.stop_NMEA_spoof()
        self.pi.wave_tx_stop()
        if self.wave is not None:
            self.pi.wave_delete(self.wave)
