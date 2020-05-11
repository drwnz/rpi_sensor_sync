# Raspberry Pi Sensor Synchronization Tool

This is a simple tool for synchronization of LiDAR and camera sensors using a 1PPS signal, either generated internally or from an attached GNSS unit.

## Use case scenarios

* Synchronize LiDAR and multiple cameras using a generated 1PPS and synchronized, phase and frequency adjustable camera trigger waveforms. The LiDAR can also be sent spoofed NMEA sentences.
* Synchronize output waveforms to an input 1PPS from a GNSS receiver.

## Getting started

### Prerequisites

You will require the following hardware:
- Raspberry Pi (tested on Raspberry Pi 4 Model B)
- Pre-installed Rasbian OS (tested on Raspbian Buster)
- LiDAR sensor that synchronizes to a 1PPS (pulse per second) signal (tested with Velodyne Alpha Prime)
- One or more sensors (i.e. cameras) that are triggered to capture with a TTL rising edge (tested with FLIR Grasshopper)

### Installing

This tool is python-based and makes use of the `pigpio` library.

Start by downloading and installing `pigpio` on the Raspberry Pi:

```
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
```

Then start the daemon (this must be done after every boot):

```
sudo pigpiod
```

### Running synchronization

Now you can connect the sensor triggers/PPS to the desired Raspberry Pi GPIO and run the synchronization script found in this repository.

```
https://github.com/drwnz/rpi_sensor_sync
```

Configure as required in `sync_config.py` (see details below) and run:

```
python run_sync.py
```

### Configuration

#### Case 1: No GNSS available, synchronization of LiDAR(s) and camera(s)

In this case, the Raspberry Pi will generate the 1PPS for the LiDAR and synchronized camera trigger pulses.
Configuration is in `sync_config.py`.
Configure the LiDAR sensor:
- `PPS_INPUT_GPIO = -1` since there is no input PPS
- `PPS_OUTPUT_GPIO = 2` if the output 1PPS (connected to LiDAR) is connected to GPIO2 (edit to desired GPIO pin)
- `SEND_DUMMY_NMEA = True` to send a spoofed NMEA message to the LiDAR - time is Raspberry Pi software clock time and GNSS position is a placeholder
- `NMEA_DESTINATION_PORT = 10110` is the destination port (10110 is the Velodyne default)
- `NMEA_DESTINATION_HOST = '192.168.1.201'` is the IP address of the LiDAR sensor

Configure the camera(s) or other triggered sensors:
- `TRIGGER1_GPIO = 3` if the camera 1 trigger is connected to GPIO3 (edit to desired GPIO pin)
- `TRIGGER1_FREQUENCY = 10` the camera 1 trigger frequency in Hz
- `TRIGGER1_PHASE = 0` the camera 1 trigger phase in degrees clockwise (see notes about phase below)

The other camera(s) are configured in the same fashion.

#### Case 2: GNSS available, synchronization of LiDAR(s) and camera(s)
In this case, the Raspberry Pi will synchronize to the 1PPS of the GNSS, which must be connected on a GPIO pin. The GNSS 1PPS can be connected directly to the LiDAR as well, or the `PPS_OUTPUT_GPIO` can be used if connected to the Raspberry Pi.
Configuration is in `sync_config.py`.
Configure the LiDAR sensor:
- `PPS_INPUT_GPIO = 10` if the input 1PPS (from GNSS) is connected to GPIO10
- `PPS_OUTPUT_GPIO = 2` if the output 1PPS (connected to LiDAR) is connected to GPIO2 (edit to desired GPIO pin)
- `SEND_DUMMY_NMEA = False` if the GNSS is connected directly to the LiDAR

Configure the camera(s) or other triggered sensors:
- `TRIGGER1_GPIO = 3` if the camera 1 trigger is connected to GPIO3 (edit to desired GPIO pin)
- `TRIGGER1_FREQUENCY = 10` the camera 1 trigger frequency in Hz
- `TRIGGER1_PHASE = 0` the camera 1 trigger phase in degrees clockwise (see notes about phase below)

The other camera(s) are configured in the same fashion.

#### Notes on trigger phase

The standard Velodyne phase configuration is alignment of the laser firing along the Velodyne Y-axis (the direction pointing away from the cable entry point) with the 1PPS rising edge. This can be configured in the web UI.
If the trigger phase of a camera is set to 0, it will fire exactly as the LiDAR lasers reach the Y-axis direction.
The phase of each camera should be set such that the capture time corresponds to when the LiDAR 'sweeps' the direction the camera is facing. For example, for a forward facing camera with a narrow FoV, a phase of 0 is probably about right, as the camera exposure time is typically much shorter than the laser sweep time over the FoV. For a rearward facing camera, the phase should be set to about 180 - again precise phase timing depends on the exposure time and FoV.
