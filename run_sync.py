#!/usr/bin/env python

import pigpio
import sync_config as cfg
from sync_tools import sync_generator
from sync_tools import serial_forwarder
from sync_tools import utils


pi = pigpio.pi()
if not pi.connected:
    exit(0)

generator = sync_generator.waveform_engine(pi)

if cfg.PPS_INPUT_GPIO != -1:
    generator.set_PPS_input_gpio(cfg.PPS_INPUT_GPIO)
    print("Input PPS signal on GPIO%d"%cfg.PPS_INPUT_GPIO)

if cfg.PPS_OUTPUT_GPIO != -1:
    generator.set_PPS_output_gpio(cfg.PPS_OUTPUT_GPIO)
    print("Output PPS signal on GPIO%d"%cfg.PPS_OUTPUT_GPIO)

for output_trigger_gpio, output_trigger_frequency, output_trigger_phase in zip(cfg.TRIGGER_GPIOS, cfg.TRIGGER_FREQUENCIES, cfg.TRIGGER_PHASES):
    if output_trigger_gpio != -1:
        generator.add_trigger_gpio(output_trigger_gpio, output_trigger_frequency, output_trigger_phase)
        print("Output trigger signal on GPIO%d with frequency %dHz and phase %d degrees"%(output_trigger_gpio, output_trigger_frequency, output_trigger_phase))

if cfg.USE_SYNC and cfg.PPS_INPUT_GPIO != -1 and cfg.PPS_OUTPUT_GPIO != -1:
    generator.start_PPS_input_sychronization()
    print("Synchronizing to input PPS pulse")

if cfg.SEND_DUMMY_NMEA and cfg.SEND_REAL_NMEA:
    print("Can't send both real and fake NMEA messages - defaulting to forward NMEA over serial")

if cfg.SEND_DUMMY_NMEA and cfg.USE_SYNC and not cfg.SEND_REAL_NMEA:
    for nmea_destinaton_host, nmea_destination_port in zip(cfg.NMEA_DESTINATION_HOSTS, cfg.NMEA_DESTINATION_PORTS):
        if utils.check_ip_port_open(nmea_destinaton_host, nmea_destination_port) and nmea_destinaton_host != -1 and nmea_destination_port != -1:
            generator.add_NMEA_spoof_device(nmea_destinaton_host, nmea_destination_port)
            print("Generating (fake) NMEA messages on ".format(nmea_destinaton_host, nmea_destination_port))
        else:
            print("Device with IP: {} on port: {} is not responding. Cannot spoof NMEA sentence.".format(nmea_destinaton_host, nmea_destination_port))

if cfg.SEND_REAL_NMEA:
    nmea_forwarder = serial_forwarder.serial_forward()
    nmea_forwarder.configure_serial(cfg.UART_PORT, cfg.UART_BAUDRATE, cfg.UART_PARITY, cfg.UART_STOPBITS, cfg.UART_BYTESIZE, cfg.UART_TIMEOUT)

    for nmea_destinaton_host, nmea_destination_port in zip(cfg.NMEA_DESTINATION_HOSTS, cfg.NMEA_DESTINATION_PORTS):
        if utils.check_ip_port_open(nmea_destinaton_host, nmea_destination_port) and nmea_destinaton_host != -1 and nmea_destination_port != -1:
            nmea_forwarder.add_destination(nmea_destinaton_host, nmea_destination_port)
            print("Forwarding NMEA messages from serial on ".format(nmea_destinaton_host, nmea_destination_port))
        else:
            print("Device with IP: {} on port: {} is not responding. Cannot forward NMEA sentence.".format(nmea_destinaton_host, nmea_destination_port))

    nmea_forwarder.daemon = True
    nmea_forwarder.start()

generator.update()

while True:
    cancel = raw_input("To stop signal IO, press 'q' then 'enter' at any time ")
    if cancel == 'q' :
        print("Shutting down signals, exiting...")
        break

generator.cancel()
pi.stop()
