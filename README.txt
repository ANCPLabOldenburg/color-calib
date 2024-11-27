################ FINDING THE USB PORT ################ 
you must first find out at which port the pr650 is mounted. 
lsusb gives you a hint of its name -> e.g. pl2303 is the driver used
dmesg | grep pl2303 | grep -oE 'ttyUSB[^. ]*
gives the USB port
The program needs the device path e.g. /dev/ttyUSB1

Normal users do not access to the port. You must set the permission to 
sudo chmod 666 /dev/ttyUSB0
or make it permanent
sudo edit /etc/udev/rules.d/50-myusb.rules
KERNEL=="ttyUSB[0-9]*",MODE="0666"
KERNEL=="ttyACM[0-9]*",MODE="0666" 

################ OUTPUT DATA STRUCTURE################   
In order to keep the data iterable we will save the output structure as numpy array. Each row is a measurement. The sequence of measurementa looks like this:

['X','Y','Z','x','y','u,'v','temperature','deviation','intensity','380', '384', '388', '392', '396', '400', '404', '408', '412', '416', '420', '424', '428', '432', '436', '440', '444', '448', '452', '456', '460', '464', '468', '472', '476', '480', '484', '488', '492', '496', '500', '504', '508', '512', '516', '520', '524', '528', '532', '536', '540', '544', '548', '552', '556', '560', '564', '568', '572', '576', '580', '584', '588', '592', '596', '600', '604', '608', '612', '616', '620', '624', '628', '632', '636', '640', '644', '648', '652', '656', '660', '664', '668', '672', '676', '680', '684', '688', '692', '696', '700', '704', '708', '712', '716', '720', '724', '728', '732', '736', '740', '744', '748', '752', '756', '760', '764', '768', '772', '776', '780','quality', 'units','screen_R','screen_G','screen_B','screen_gamma','screen_brightness','screen_contrast','screen_temperature']

X,Y,Z: 		Corresponding CIE 1931 coordinates. Y is luminance in cd*m^2 if 'unit' is 0
x,y:		CIE 1931 x and y. For luminane see 'Y'
u,v: 		CIE 1931 u' and v'.  For luminane see 'Y'
temperature:CIE correlated color temperature in K.
deviation:  From Black body. Positive means color is above expected curve in xy-plane 
intensity:  Integral over spectrum. Spectral radiance in W*m^-2*sr^-1*nm^-1 if 'unit' is 0.
380-780:	Spectral radiance at specific wavelength intervals
quality:    Measurement quality: 0 is good
screen_*:   Settings of the screen when measurement was taken. See next scetion for an explanation

################ CALIBRATION ################   

Before starting the calibration screen settings should be passed to the calibration program. They will be saved with the measurements. Pass 'nan' if you don't know them.
WARNING: The color profile will not work if you change any of these settings!!!

For Xorg screen paramters can be read with tools like xgamma or xrandr --verbose. Best is to keep software Gamma and Brightness at 1.0. The transform matrix should be an identity matrix (i.e. diagonal entries are 1.0 rest are 0.0) and _ICC_PROFILE is unloaded or doe not exist for that screen.

For screens with their own controls pass them to the program in order to save them     


