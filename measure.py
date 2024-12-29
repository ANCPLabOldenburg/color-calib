"""
USER PARAMTERS
""" 

pr650_port="/dev/ttyUSB0" #This depends on your setup
#name format MonitorOnComputerXXPointsXXBrightnessXXContrastXXGamma_YYYYMMDD
monitor_name='MonitorOnComputerXXPointsXXBrightnessXXContrastXXGamma_YYYYMMDD' #This will be the file name 
#monitor_name='P14sPlatypus853PointsBrightness50_20241209' #This will be the file name 
monitor_setting_contrast=100 # The setting at the monitor 
monitor_setting_brightness=50 # The setting at the monitor. Try to adjust to ca 200 cd/m^2
monitor_seting_color_temperature=6500 # The setting at the monitor
monitor_gamma=1.0 # The setting at the monitor
monitor_comment='This is some descriptive text' 
ambient_light_level_cdm2=0 #This is only relevant 
color_ramp_type='ti1' #One of 'equal_steps' 'dark_augmented' 'lo'g 'ti1'. ti1 requires the file name specified
ti1_file='852Patches.ti1'
#Output from xrandr --verbose
X_r_gamma=1.0
X_g_gamma=1.0
X_b_gamma=1.0
X_brightness=1.0
X_matrix=[[1.0, 0.0, 0.0],[0.0, 1.0, 0.0],[0.0, 0.0, 1.0]]
X_icc_loaded=True

""" 
Prepare measurement 
"""
from pr650 import pr650
import numpy as np
import time
import dill

# Set up pr650 
device=pr650() 
device.open_pr650(pr650_port) # this intializes the device 
# Set up color ramps
if color_ramp_type == 'dark_augmented':
	cols = device.make_color_ramp_from_array(device.color_ramp_dark_augmented)
elif color_ramp_type == 'equal_steps':
	cols = device.make_color_ramp_from_array(device.color_ramp_equal_steps)
elif color_ramp_type == 'log':
	cols = device.make_color_ramp_from_array(device.color_ramp_log)
elif color_ramp_type =='ti1':
	cols=device.read_rgb_from_ti1(ti1_file) 
else:
	print('Unkown color ramp type: ', color_ramp_type)
	print('Choose one of: dark_augmented, equal_steps, log')
	sys.exit()
#Initialize the array to store the measurements
# TOO: integrate in generation of color ramps
device.make_values_array(cols)
#Set up drawing rectangles
device.make_rectangle() 

"""
User adjusts figure and starts
"""

print("Adjust figure position and PR650.Then press a key to start measurement.")
input()
print("Starting measuremnt")

"""
Start measuring
"""

# loop over RGB array
for k in np.arange(np.shape(cols)[0]):
	print("Next color: ", cols[k,:]/255)
	device.set_rectangle_color(cols[k,:])
	#Take a measurement. Do this only once per color 
	device.com.read(device.com.inWaiting()) #empty reponse queue	
	device.send_to_pr650(device.commands['measure']+device.response_codes['lum_x_y_u_v']+device.command_terminator) 
	#Wait until the measurement is done and PR650 can return something
	while '' == str(device.com.read(device.com.inWaiting()),'utf-8'):
		time.sleep(1)
	#Read lum_x_y_u_v data
	response=device.receive_from_pr650(device.response_codes['lum_x_y_u_v'])
	print("lum_x_y_u_v: ", response)
	#  Parse lum_x_y_u_v data
	Y,x,y,u,v,quality,unit=device.parse_lum_x_y_u_v(response)
	#Read lum_x_y_u_v data
	response=device.receive_from_pr650(device.response_codes['XYZ'])
	print("XYZ: ", response)
	#  Parse XYZ data
	X,Y,Z,quality,unit=device.parse_XYZ(response)
	#Read lum_temp_deviaton data
	response=device.receive_from_pr650(device.response_codes['lum_temp_deviation'])
	print("lum_temp_deviation: ", response)
	#Parse lum_temp_deviaton data
	Y,temp,deviation,quality,unit=device.parse_lum_u_v(response)
	#Read spectral data 
	response=device.receive_from_pr650(device.response_codes['spectrum'])
	print("spectrum: ", response)
	#ipdb.set_trace()
	#Parse spectral data
	spectral_i, wavelength, intensity, quality, unit=device.parse_spectrum(response) 
	if quality ==float(device.response_checks['default_ok']):
		print(cols[k,:], 'quality OK: ', float(device.response_checks['default_ok']))
	else:
		print(cols[k,:], 'quality NOT OK: ', quality)
	"""
	Store data in result array
	"""
	device.values[k,device.indices['colors']]=cols[k,:]
	device.values[k,device.indices['XYZ']]= [X,Y,Z]
	device.values[k,device.indices['x_y']]=[x,y]
	device.values[k,device.indices['u_v']]=[u,v]
	device.values[k,device.indices['temp_deviation']]=[temp,deviation]
	device.values[k,device.indices['quality_unit']]=[quality,unit]
	device.values[k,device.indices['intensity']]=intensity
	device.values[k,device.indices['spectral_i']]=spectral_i

# save results 
np.savetxt(monitor_name+'.txt', device.values,fmt='%.9e')
dill.dump_session(monitor_name+'.dill')


#THIS CREATES AN ICC-Profile. Expects Argyll CMS on the shell path 
#First make a ti3 file 
import make_ti3_file as ti3
ti3.create_ti3_from_measurement_file(monitor_name+'.txt',monitor_name+'.ti3')
import subprocess
subprocess.run(["colprof", "-v -qh -as -nc -D", f"{monitor_name}","","-O",f"{monitor_name}"])
print(f"Wrote {monitor_name}.icc")
print(f"To activate ICC profile run 'cp {monitor_name}.icc ~/.local/share/icc/' and activate in color profile manager")

#A simpler profile that seems to work
#~/Downloads/Argyll_V3.3.0/bin/colprof -v -qh -as -nc -D "P14sPlatypus853PointsBrightness50_20241209-qh-as-nc" -O P14sPlatypus853PointsBrightness50_20241209-qh-as-nc.icc ~/Programing/Python/color-calib/P14sPlatypus853PointsBrightness50_20241209

#A complex profile that darktable seems to have problems with
#~/Downloads/Argyll_V3.3.0/bin/colprof -v -D "Monitor ICC Profile" ~/Programing/Python/color-calib/P14sPlatypus

#Apply ICC Profile in color management 

#Create test patches
#targen -v -d 3 testPatches

#dispwin -d 1 -L ~/.local/share/icc/P14sPlatypusBrightness100.icc 
