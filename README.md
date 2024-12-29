# Monitor Color Calibration 
### with a PR 650 spectroradiometer
This repo implements the workflow and the functionality required to automatcally characterize luminance, CIE and spectral color responses of a monitor. The results can be used to create an ICC profile for the monitor with [Argyll CMS](https://www.argyllcms.com/). The core script will do that if 'colprof' is on the binary path. Otherwise you are left with the measurements. You can always run 'colprof' later.  

The code was written because available tools did not support the Spectrascan PR 650 spectroradiometer (a fact, not a complaint). It comprises all steps from setting up the measurement device, having a set to RGB values to measure, loop ing over the list displaying each color on the screen, taking a measurement, stornig the data, writing them to a ti3 file Argyll's coloprof can use to write an ICC profile.\n
Others might find this repo a useful starting point (issues/pull requests welcome) to 
a) use their own PR 650 for monitor profiling or calibration 
b) adapt the code to support more previously unsupported colorimeters or spectroradiometers.
The only thing that is needed from the device are the CIE 1931 XYZ coordinates for each color patch measured and a communication protocol to control the device 
The results can be used to create an ICC profile for the monitor with [Argyll CMS](https://www.argyllcms.com/)

## How to:
1. Connect the PR650 to the serial port of you computer. This is likely done with a Serial-USB convert er.
2. Find the port te PR 650 is connected to and enter it as user parameter im measure.py. 
   In Linux you can find the port like this:
   2.a. lsusb gives you a hint of its name -> e.g. pl2303 is the driver used
   2.b. dmesg | grep pl2303 | grep -oE 'ttyUSB[^. ]*
        gives the USB port. The last result line is the what you want
   2.c. Enter the device path in measure.py e.g. '/dev/ttyUSB0'
   In Windows you can look in the device manager
3. Under linux make sure you have write access to the port. If it is only writable for root use (with the appropriate path)
   sudo chmod 666 /dev/ttyUSB0
4. Set you monitor controls and document them in measure.py. Most often contrast is set to 100, color temperature is set to daylight 6500 K and the luminance is reduced to ca 200 cd/m^2 at white if you use the calibration for photo proofing. This is approximately the luminace you get from photo paper under normal light conditions. Gamma setting can be at 2.2 whic is the standard. Check if any other unknown settings are enabled
5. For an initial measurement unload loaded ICC profiles.
6. Turn the Pr650 and start measure.py from a Ipython command prompt as long as 'CMD' is visible in PR 650's display. If things went well the display light should be turned on and 'CMD' is turned into 'S'. On the moitor a figure with a color patch is visible. If not check the python command window for hints
7. Place the window at the center of the screen and focus the PR 650.
8. If possibles darken the room and start the measuremnt.
9. After the measurment is finished all data will be saved to a *.dill and and ICC profile will be created if you have 'colprof' from [Argyll CMS](https://www.argyllcms.com/) on your binary path 

## Contents
**measure.py** is the starting point and implements the whole workflow. It comprises the **[editable] basic user definitions**, the measurement control flow, the creation of an intermediate result file (Argyll *.ti3 format) and **provides command line code to write an ICC profile from the measurement**.

**852Patches.ti1** defines the rgb values of 852 color patches that can be used to claibrate a monitor. It might a bit too detailed but since the measurement runs automatically that should not matter too much. I was was created with Agyll's command 'targen -v -d 3 852Patches' 

**pr650.py** implements a class to remote control the PR 650 spectroradiometer to take measurements and the data definitions.

**make_ti3_file.py** functions to write a *ti3 file from the measurements. Argyll can use this file format to create a monitor ICC profile 

## Dependencies:

serial  Communication with PR 650
matplotlib  Display the color patches
numpy   Data structures and handling
dill    Dump all variables of a session. Not elegant but effective.
time    Timers
subprocess  Run Argyll commands from within python
[Argyll CMS](https://www.argyllcms.com/)   A suite of software tools for color management. Unfortunately it does not support the PR 650 
