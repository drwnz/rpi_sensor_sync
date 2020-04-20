#!/usr/bin/env python

import pigpio
from sync_tools import sync_generator

PPS_INPUT_GPIO = -1         # 0-31. Use -1 for inactive
PPS_OUTPUT_GPIO = 2         # 0-31. Use -1 for inactive

TRIGGER1_GPIO = 3           # 0-31. Use -1 for inactive
TRIGGER2_GPIO = 4
TRIGGER3_GPIO = 5
TRIGGER4_GPIO = 6
TRIGGER5_GPIO = 7
TRIGGER6_GPIO = 8

TRIGGER1_FREQUENCY = 10     # Integer number in Hertz
TRIGGER2_FREQUENCY = 10
TRIGGER3_FREQUENCY = 10
TRIGGER4_FREQUENCY = 10
TRIGGER5_FREQUENCY = 10
TRIGGER6_FREQUENCY = 10

TRIGGER1_PHASE = 30          # 0-360 in degrees
TRIGGER2_PHASE = 90
TRIGGER3_PHASE = 150
TRIGGER4_PHASE = 210
TRIGGER5_PHASE = 270
TRIGGER6_PHASE = 330

USE_SYNC = False             # Enable synchronization to PPS input when available
SEND_DUMMY_NMEA = False      # Enable spoof NMEA messages
NMEA_DESTINATION_PORT = 10110
NMEA_DESTINATION_HOST = '192.168.1.201'

TRIGGER_GPIOS = [TRIGGER1_GPIO, TRIGGER2_GPIO, TRIGGER3_GPIO,
                    TRIGGER4_GPIO, TRIGGER5_GPIO, TRIGGER6_GPIO]

TRIGGER_FREQUENCIES = [TRIGGER1_FREQUENCY, TRIGGER2_FREQUENCY, TRIGGER3_FREQUENCY,
                        TRIGGER4_FREQUENCY, TRIGGER5_FREQUENCY, TRIGGER6_FREQUENCY]

TRIGGER_PHASES = [TRIGGER1_PHASE, TRIGGER2_PHASE, TRIGGER3_PHASE,
                    TRIGGER4_PHASE, TRIGGER5_PHASE, TRIGGER6_PHASE]


pi = pigpio.pi()
if not pi.connected:
    exit(0)

generator = sync_generator.waveform_engine(pi)

if (PPS_INPUT_GPIO != -1):
    generator.set_PPS_input_gpio(PPS_INPUT_GPIO)
    print ("Input PPS signal on GPIO%d"%PPS_INPUT_GPIO)

if (PPS_OUTPUT_GPIO != -1):
    generator.set_PPS_output_gpio(PPS_OUTPUT_GPIO)
    print ("Output PPS signal on GPIO%d"%PPS_OUTPUT_GPIO)

for output_trigger_gpio, output_trigger_frequency, output_trigger_phase in zip(TRIGGER_GPIOS, TRIGGER_FREQUENCIES, TRIGGER_PHASES):
    generator.add_trigger_gpio(output_trigger_gpio, output_trigger_frequency, output_trigger_phase)
    print ("Output trigger signal on GPIO%d with frequency %dHz and phase %d degrees"%(output_trigger_gpio, output_trigger_frequency, output_trigger_phase))

if USE_SYNC and PPS_INPUT_GPIO != -1 and PPS_OUTPUT_GPIO != -1:
    generator.start_PPS_input_sychronization()
    print ("Synchronizing to input PPS pulse")

if SEND_DUMMY_NMEA and USE_SYNC:
    generator.start_NMEA_spoof(NMEA_DESTINATION_PORT, NMEA_DESTINATION_HOST)
    print ("Generating (fake) NMEA messages")

generator.update()

while True:
    cancel = raw_input("To stop signal IO, press 'q' then 'enter' at any time ")
    if cancel == 'q' :
        print ("Shutting down signals, exiting...")
        break

generator.cancel()
pi.stop()
