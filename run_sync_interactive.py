#!/usr/bin/env python

import pigpio
from sync_tools import sync_generator

input_PPS_gpio = None
PPS_in = -1
output_PPS_gpio = None
PPS_out = -1

trigger_out = []

while not input_PPS_gpio:
    input_PPS_gpio = raw_input("Enter input PPS GPIO identifier (0-31, n if not used): ")
    if input_PPS_gpio == 'n':
       pass
    elif input_PPS_gpio.isdigit() and 0 <= int(input_PPS_gpio) < 32:
        PPS_in = int(input_PPS_gpio)
        input_PPS_gpio = True
    else:
        input_PPS_gpio = None
        print("Enter an integer between 0 and 31, or n for none")

while not output_PPS_gpio:
    output_PPS_gpio = raw_input("Enter output PPS GPIO identifier (0-31, n if not used): ")
    if output_PPS_gpio == 'n':
        pass
    elif output_PPS_gpio.isdigit() and 0 <= int(output_PPS_gpio) < 32 and int(output_PPS_gpio) != PPS_in:
        PPS_out = int(output_PPS_gpio)
        output_PPS_gpio = True
    else:
        input_PPS_gpio = None
        print("Enter an integer between 0 and 31 that has not already been used, or n for none")

num_triggers = 0
input_num_triggers = None
while not input_num_triggers:
    input_num_triggers = raw_input("Enter number of output trigger signals (1-20, n if not used): ")
    if input_num_triggers == 'n' or input_num_triggers == '0':
        pass
    elif input_num_triggers.isdigit() and 0 < int(input_num_triggers) < 21:
        num_triggers = int(input_num_triggers)
        input_num_triggers = True
    else:
        input_num_triggers = None
        print("Enter an integer between 0 and 20, or n for none")

trigger_out = []

for i in range(num_triggers):
    output_trigger_gpio = None
    while not output_trigger_gpio:
        output_trigger_gpio = raw_input("Enter output trigger %d GPIO identifier (0-31, n if not used): "%i)
        if output_trigger_gpio == 'n':
            pass
        elif output_trigger_gpio.isdigit() and 0 <= int(output_trigger_gpio) < 32 and int(output_trigger_gpio) != PPS_in and int(output_trigger_gpio) != PPS_out:
            trigger_gpio = int(output_trigger_gpio)
            output_trigger_frequency = None
            trigger_frequency = 1
            while not output_trigger_frequency:
                output_trigger_frequency = raw_input("Enter output trigger %d frequency: "%i)
                if output_trigger_frequency.isdigit() and 0 < int(output_trigger_frequency) < 10001:
                    trigger_frequency = int(output_trigger_frequency)
                    output_trigger_frequency = True
                else:
                    output_trigger_frequency = None
                    print("Enter an integer between 0 and 1000")
            output_trigger_phase = None
            trigger_phase = 0
            while not output_trigger_phase:
                output_trigger_phase = raw_input("Enter output trigger %d phase in degrees: "%i)
                if output_trigger_phase.isdigit() and 0 <= int(output_trigger_phase) < 361:
                    trigger_phase = int(output_trigger_phase)
                    output_trigger_phase = True
                else:
                    output_trigger_phase = None
                    print("Enter an integer between 0 and 360")
            trigger_out.append((trigger_gpio, trigger_frequency, trigger_phase))
        else:
            output_trigger_gpio = None
            print("Enter an integer between 0 and 31 that has not already been used, or n for none")

syc_option = None
use_sync = False
if (PPS_in != -1) and (PPS_out != -1):
    while not sync_option:
        sync_option = raw_input("Synchronize to input PPS? y = yes, n = no: ")
        if sync_option == 'y':
            use_sync = True
            syc_option = True
        elif sync_option == 'n':
            use_sync = False
            sync_option = True
        else:
            print("Enter either 'y' for yes or 'n' for no")
            sync_option = None


pi = pigpio.pi()
if not pi.connected:
    exit(0)

generator = sync_generator.waveform_engine(pi)

if (PPS_in != -1):
    generator.set_PPS_input_gpio(PPS_in)
    print ("Input PPS signal on GPIO%d"%PPS_in)

if (PPS_out != -1):
    generator.set_PPS_output_gpio(PPS_out)
    print ("Output PPS signal on GPIO%d"%PPS_out)

for output_trigger in trigger_out:
    generator.add_trigger_gpio(output_trigger[0], output_trigger[1], output_trigger[2])
    print ("Output trigger signal on GPIO%d with frequency %dHz and phase %d degrees"%(output_trigger[0], output_trigger[1], output_trigger[2]))

if use_sync:
    generator.start_PPS_input_sychronization()
    print ("Synchronizing to input PPS pulse")

generator.update()

while True:
    cancel = raw_input("To stop signal IO, press 'q' then 'enter' at any time ")
    if cancel == 'q' :
        print ("Shutting down signals, exiting...")
        break

generator.cancel()
pi.stop()
