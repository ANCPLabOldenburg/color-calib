import serial, time 
import numpy as np
from  matplotlib import pyplot as plt
import dill
import sys 
import ipdb

class pr650():

	def __init__(self, port="/dev/ttyUSB0"):
		self.port=port
		self.command_terminator='\r'
		self.response_codes={'lum_x_y':'1',
							'XYZ':'2',
							'lum_u_v':'3',
							'lum_temp_deviation':'4',
							'spectrum':'5',
							'lum_x_y_u_v':'6'
							}

		self.commands={'backlight_on':'B2',
						'backlight_off':'B0',
						'measure':'M',
						'receive_data':'D',
						'set_up_measurements':'S'
						}
		self.setups={'normal-lens_adaptive-intergation_one-measuremnt_units-candela*m^2-or-lux':'1,,,,,0,,1'}

		self.response_checks={'default_ok':'000\r\n',
								'measurement_setup_ok':'00\r\n' 
						}
 		
		# open the serial port to  
		try:
			self.com=serial.Serial(self.port,9600, timeout=10) #open the port
			time.sleep(1)
			self.com.read(self.com.inWaiting())#empty send buffer
			self.com.write(str.encode(self.commands['backlight_on']+self.command_terminator))#display light on to bring pr650 in remote mode
			time.sleep(1)
			answer=str(self.com.read(self.com.inWaiting()),'utf-8') #The response is a bytes_string. The outer str() turns it into a regular ascii string
			print("Port write OK: Opened port %s" %self.port)
			print("Answer: ", answer)
		except:
			print("Port write failed: Could not open serial port %s" %self.port)
			print("1) Check if the port is correct")
			print("2) Check permissions. You may have to run")
			print("sudo chmod 666 %s" %self.port)
			self.com.close()
			print(sys.exc_info()[1])
			sys.exit()

		#test if communication works
		if answer != self.response_checks['default_ok']:
			print("Port read failed: PR650 does not send data!")
			print("Received: ", answer, " expected: ", self.response_checks['default_ok'])  
			print("Closing connection!")
			self.com.close()
			print(sys.exc_info()[1])
			sys.exit()
		else: #If it worked set up measurement 
			print("Port read OK: PR650 sends data!")
			print("Received: ", answer, " expected: ", self.response_checks['default_ok'])

		#Set up  measurement
		time.sleep(1)
		self.com.read(self.com.inWaiting())#empty send buffer
		self.com.write(str.encode(self.commands['set_up_measurements']+
							self.setups['normal-lens_adaptive-intergation_one-measuremnt_units-candela*m^2-or-lux']+
							self.command_terminator
				))
		time.sleep(1)
		answer=str(self.com.read(self.com.inWaiting()),'utf-8')
		if answer != self.response_checks['measurement_setup_ok']:
			print("Measurement setup failed!")
			print("Received: ", answer, " expected: ", self.response_checks['default_ok'])
			print("Closing connection!")
			self.com.close()
			print(sys.exc_info()[1])
			sys.exit()
		else: 
			print("Measurement parameters set up!")
			print("Measurement units cd*m^2 or lux")  	

	def send_to_pr650(self,command):
			self.com.read(self.com.inWaiting()) #empty the response buffer
			self.com.write(str.encode(command+self.command_terminator))
			return None

	def receive_from_pr650(self, response_code):
			self.com.read(self.com.inWaiting()) #empty the response buffer
			time.sleep(1)
			self.send_to_pr650(self.commands['receive_data']+response_code+self.command_terminator)
			time.sleep(1)
			if response_code == self.response_codes['spectrum']:
				response = self.com.readlines()
			else:
				response=self.com.read(self.com.inWaiting())		
			#Call the appropriate parser
			#key = {i for i in self.response_codes if self.response_codes[i]==response_code} #get the dictionary key 
			#parser = getattr(self, 'parse+_'+key) 
			#response_array=parser(response)
			#return response_array
			return response 

	def parse_lum_x_y(self,response):
		"""
			Parse the result of a luminance, x, y, measurement

			Inputs:
			response: 	A list containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			Y:			The luminance in cd*m^2 if unit is 0 (float)
			x:			CIE 1931 coordinate (float)
			y:			CIE 1931 coordinate (float)
			quality:	0 if measurement quality was good (float)
			unit:		cd*m^2 for Y if 0 (float)
		"""

		response_string=str.split(str(response,'utf-8'),',') 
		quality=float(response_string[0])
		unit=float(response_string[1])
		Y=float(response_string[2])
		x=float(response_string[3])
		y=float(response_string[4])
		return Y,x,y,quality,unit

	def parse_XYZ(self,response):
		"""
			Parse the result of a X,Y, and Z measurement.

			Inputs:
			response: 	A list containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			X:			CIE 1931 coordinate (float)
			Y:			The luminance in cd*m^2 if unit is 0 (float)
			Z:			CIE 1931 coordinate (float)
			quality:	0 if measurement quality was good (float)
			unit:		cd*m^2 for Y if 0 (float)
		"""
		response_string=str.split(str(response,'utf-8'),',') 
		quality=float(response_string[0])
		unit=float(response_string[1])
		X=float(response_string[2])
		Y=float(response_string[3])
		Z=float(response_string[4])
		return X,Y,Z,quality,unit

	def parse_lum_u_v(self,response):
		"""
			Parse the result of a luminance, u', v' measurement

			Inputs:
			response: 	A list containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			Y:			The luminance in cd*m^2 if unit is 0 (float)
			u:			CIE 1931 coordinate (float)
			v:			CIE 1931 coordinate (float)
			quality:	0 if measurement quality was good (float)
			unit:		cd*m^2 for Y if 0 (float)
		"""
		response_string=str.split(str(response,'utf-8'),',') 
		quality=float(response_string[0]) # get the values
		unit=float(response_string[1])
		Y=float(response_string[2])
		u=float(response_string[3])
		v=float(response_string[4])
		return Y,u,v,quality,unit

	def parse_lum_temp_deviaton(self,response):
		"""
			Parse the result of a luminance, color temperature, and black body deviation measurement

			Inputs:
			response: 	A list containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			Y:			The luminance in cd*m^2 if unit is 0 (float)
			temp:		Correlated color temparature in K (float)
			deviation:	Deviation from black body in CIE1960 uv units. Positive is above locus. (float)
			quality:	0 if measurement quality was good (float)
			unit:		cd*m^2 for Y if 0 (float)
		"""

		response_string=str.split(str(response,'utf-8'),',') #segment response string 
		quality=float(response_string[0]) # get the values
		unit=float(response_string[1])
		Y=float(response_string[2])
		temp=float(response_string[3])
		deviation=float(response_string[4])
		return Y,temp,deviation,quality,unit

	def parse_spectrum(self,response):
		"""
			Parse the result of a spectral measurement

			Inputs:
			response: 	A list of lists containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			spectral_i:	Spectral intensity (numpy array float)
			wavelength: wavelength in nm (numpy array float)
			intensity:	Integrated intensity as the integral over the spectrum (float)
			quality:	0 if measurement quality was good (float)
			unit:		cW*m^-2*sr^-1^nm^-1 if  0 (float)
		"""

		quality=float(str.split(str(response[0],'utf-8'),',')[0]) # two strings in this sub-list
		unit=float(str.split(str(response[0],'utf-8'),',')[1])
		intensity= float(str(response[1],'utf-8')) # one string in this sub-list
		wavelength=np.array([])
		spectral_i=np.array([])
		for k in range(2,len(response)):
			wavelength=np.append(wavelength,float(str.split(str(response[k],'utf-8'),',')[0]))
			spectral_i=np.append(spectral_i,float(str.split(str(response[k],'utf-8'),',')[1]))
		return spectral_i, wavelength, intensity, quality, unit 

	def parse_lum_x_y_u_v(self,response):
		"""
			Parse the result of a luminance, x,y,u,v measurement

			Inputs:
			response: 	A list containing the byte_like returned from receive_from_pr650 with corresponding response code 

			Outputs:
			Y:			The luminance in cd*m^2 if unit is 0 (float)
			x:			CIE 1931 coordinate (float)
			y:			CIE 1931 coordinate (float)
			u:			CIE 1976 coordinate (float)
			v:			CIE 1976 coordinate (float)
			quality:	0 if measurement quality was good (float)
			unit:		cd*m^2 for Y if 0 (float)
		"""

		response_string=str.split(str(response,'utf-8'),',') #segment response string 
		quality=float(response_string[0]) # get the values
		unit=float(response_string[1])
		Y=float(response_string[2])
		x=float(response_string[3])
		y=float(response_string[4])
		u=float(response_string[5])
		v=float(response_string[6])
		return Y,x,y,u,v,quality,unit

"""
USER PARAMTERS
""" 

pr650_port="/dev/ttyUSB1"
monitor_name='T440pPlatypus_20241126' #This will be the file name 
monitor_setting_contrast=100
monitor_setting_brightness=100
monitor_seting_color_temperature=5000
ambient_light_level_cdm2=0
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

# Set up pr650 
device=pr650(pr650_port) # this intializes the device 
# set up RGB array
color_ramp=np.array([0],ndmin=2)
color_ramp=np.append(color_ramp,(np.round(np.cumproduct(np.repeat(1.45,14)))))
color_ramp=np.append(color_ramp,255)
red_ramp=np.zeros([len(color_ramp),3])
red_ramp[:,0]=color_ramp
green_ramp=red_ramp[1:,[1,0,2]]
blue_ramp=red_ramp[1:,[1,2,0]]
colors=np.append(np.append(red_ramp,green_ramp,axis=0),blue_ramp,axis=0)
colors=np.append([[0,255,255],[255,0,255],[255,255,0],[255,255,255]],colors,axis=0)

# set up result array and indices
values=np.zeros([np.shape(colors)[0],116])
indices={'colors':[0,1,2],
		'XYZ':[3,4,5],
		'x_y':[6,7],
		'u_v':[8,9],
		'temp_deviation':[10,11],
		'quality_unit':[12,13],
		'intensity':[14],
		'spectral_i':np.arange(15,116)
		}

#Set up drawing rectangles
#%matplotlib 
#equires ipython, activates interactive plpotting in a figure that can be moved to the place where we want to measure
fig, ax = plt.subplots()
fig.set_facecolor([0,0,0]) #fgure background to black
ax.set_facecolor([0,0,0]) #axis background to black
rectangle=plt.Rectangle((0,0),1,1,facecolor=[1,1,1])
ax.add_patch(rectangle)
plt.draw()
plt.pause(1)

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
for k in np.arange(np.shape(colors)[0]):
	print("Next color: ", colors[k,:]/255)
	#Set patch color
	ax.clear()
	ax.set_facecolor([0,0,0])
	ax.axis('off')
	rectangle=plt.Rectangle((0,0),1,1,facecolor=colors[k,:]/255)
	ax.add_patch(rectangle)
	plt.draw()
	plt.pause(1)
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
		print(colors[k,:], 'quality OK: ', float(device.response_checks['default_ok']))
	else:
		print(colors[k,:], 'quality NOT OK: ', quality)
	"""
	Store data in result array
	"""
	values[k,indices['colors']]=colors[k,:]
	values[k,indices['XYZ']]= [X,Y,Z]
	values[k,indices['x_y']]=[x,y]
	values[k,indices['u_v']]=[u,v]
	values[k,indices['temp_deviation']]=[temp,deviation]
	values[k,indices['quality_unit']]=[quality,unit]
	values[k,indices['intensity']]=intensity
	values[k,indices['spectral_i']]=spectral_i
	""" #test indexes
	values[k,indices['colors']]=indices['colors']
	values[k,indices['XYZ']]=indices['XYZ']
	values[k,indices['x_y']]=indices['x_y']
	values[k,indices['u_v']]=indices['u_v']
	values[k,indices['temp_deviation']]=indices['temp_deviation']
	values[k,indices['quality_unit']]=indices['quality_unit']
	values[k,indices['intensity']]=indices['intensity']
	values[k,indices['spectral_i']]=indices['spectral_i']
	"""

# save results 
dill.dump_session(monitor_name+'.dill')

#if __name__ == "__main__":
#    sys.exit(main())

