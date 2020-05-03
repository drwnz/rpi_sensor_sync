#!/usr/bin/env python

import pigpio
from sync_tools import sync_generator

import sync_config as cfg
from sync_tools import utils


pi = pigpio.pi()
if not pi.connected:
    exit(0)

generator = sync_generator.waveform_engine(pi)

if (cfg.PPS_INPUT_GPIO != -1):
    generator.set_PPS_input_gpio(cfg.PPS_INPUT_GPIO)
    print ("Input PPS signal on GPIO%d"%cfg.PPS_INPUT_GPIO)

if (cfg.PPS_OUTPUT_GPIO != -1):
    generator.set_PPS_output_gpio(cfg.PPS_OUTPUT_GPIO)
    print ("Output PPS signal on GPIO%d"%cfg.PPS_OUTPUT_GPIO)

for output_trigger_gpio, output_trigger_frequency, output_trigger_phase in zip(cfg.TRIGGER_GPIOS, cfg.TRIGGER_FREQUENCIES, cfg.TRIGGER_PHASES):
    if output_trigger_gpio != -1:
        generator.add_trigger_gpio(output_trigger_gpio, output_trigger_frequency, output_trigger_phase)
        print ("Output trigger signal on GPIO%d with frequency %dHz and phase %d degrees"%(output_trigger_gpio, output_trigger_frequency, output_trigger_phase))

if cfg.USE_SYNC and cfg.PPS_INPUT_GPIO != -1 and cfg.PPS_OUTPUT_GPIO != -1:
    generator.start_PPS_input_sychronization()
    print ("Synchronizing to input PPS pulse")

if cfg.SEND_DUMMY_NMEA and cfg.USE_SYNC:
    if utils.check_ip_port_open(cfg.NMEA_DESTINATION_HOST, cfg.NMEA_DESTINATION_PORT):
        generator.start_NMEA_spoof(cfg.NMEA_DESTINATION_PORT, cfg.NMEA_DESTINATION_HOST)
        print ("Generating (fake) NMEA messages")
    else:
        print ("Device with IP: {} on port: {} is not responding. Cannot spoof NMEA sentence.".format(cfg.NMEA_DESTINATION_HOST, cfg.NMEA_DESTINATION_PORT))

generator.update()

while True:
    cancel = raw_input("To stop signal IO, press 'q' then 'enter' at any time ")
    if cancel == 'q' :
        print ("Shutting down signals, exiting...")
        break

generator.cancel()
pi.stop()
