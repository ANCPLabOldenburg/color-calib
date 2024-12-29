import serial, time 
import numpy as np
from  matplotlib import pyplot as plt
import sys 
import ipdb
import dill

class pr650():

	def __init__(self):
		#self.port=port
		self.pr650_connected=False
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
 		# set up ramp vectors 
		self.color_ramp_log=np.array([0],ndmin=2)
		self.color_ramp_log=np.append(self.color_ramp_log,(np.round(np.cumprod(np.repeat(1.45,14)))))
		self.color_ramp_log=np.append(self.color_ramp_log,255)
		self.color_ramp_dark_augmented=np.round(np.array([0.0, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0])*255)
		self.color_ramp_equal_steps=np.round(np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0])*255)

		# Figure and axis handles
		self.ax=[]
		self.fig=[]


		# set up result array and indices
		self.indices={'colors':[0,1,2],
				'XYZ':[3,4,5],
				'x_y':[6,7],
				'u_v':[8,9],
				'temp_deviation':[10,11],
				'quality_unit':[12,13],
				'intensity':[14],
				'spectral_i':np.arange(15,116)
				}
		self.values=np.array([])

	def make_values_array(self,cols):
		"""
			Add rows to the internal results array "values" to store the measurements. Alle entries will be filled with zeros. Thus measurements not entered by the user willshow up as exact zeros.

			Input: 
			colorr:	A numpy matrix with shape n-by-3 holding the to-be-measured color values.

			Output: None 
		"""
		
		self.values=np.zeros([np.shape(cols)[0],116])

	def open_pr650(self, port="/dev/ttyUSB0"):
		"""
			Open the serial port communication to the PR650. On succes the member pr650_connected is set to True

			Inputs:
			port:		The serial port descriptor. On linux something like: /dev/ttyUSB0 (default)

			Outputs: 	None

			Remarks:
			On linux you must first find out at which port the pr650 is mounted. 
			lsusb gives you a hint of its name -> e.g. pl2303 is the driver used
			dmesg | grep pl2303 | grep -oE 'ttyUSB[^. ]*
			gives the USB port
			The function needs the device path e.g. /dev/ttyUSB1

			Normal users do not access to the port. You must set the permission to 
			sudo chmod 666 /dev/ttyUSB0
			or make it permanent
			sudo edit /etc/udev/rules.d/50-myusb.rules
			KERNEL=="ttyUSB[0-9]*",MODE="0666"
		"""
		# open the serial port   
		try:
			self.com=serial.Serial(port,9600, timeout=10) #open the port
			time.sleep(1)
			self.com.read(self.com.inWaiting())#empty send buffer
			self.com.write(str.encode(self.commands['backlight_on']+self.command_terminator))#display light on to bring pr650 in remote mode
			time.sleep(1)
			answer=str(self.com.read(self.com.inWaiting()),'utf-8') #The response is a bytes_string. The outer str() turns it into a regular ascii string
			print("Port write OK: Opened port %s" %port)
			print("Answer: ", answer)
		except:
			print("Port write failed: Could not open serial port %s" %port)
			print("1) Check if the port is correct")
			print("2) Check permissions. You may have to run")
			print("sudo chmod 666 %s" %port)
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
		#Currently only one type supported 
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
			self.pr650_connected=True 	

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

	def make_color_ramp_from_array(self, ramp_array):
		"""
			Make a color ramp from a numpy vector. The color ramp starts at zero and ends at 255. The vector will be copied four times to create a red, green, blue, and grey ramp.a Black [0, 0 ,0] will only be included once. The colors [0,255,255],[255,0,255],[255,255,0],[255,255,255] are added to the end.	

			Inputs: 
			ramp_array: A vector with the color values. Zero must be included in the first position.

			Output:
			cols: 		A matrix holding the rgb-values of four color ramps. Black [0, 0, 0] is only oncluded in the first ramp
		"""

		red_ramp=np.zeros([len(ramp_array),3])
		red_ramp[:,0]=ramp_array
		green_ramp=red_ramp[1:,[1,0,2]]
		blue_ramp=red_ramp[1:,[1,2,0]]
		grey_ramp=np.vstack((green_ramp[:,1],green_ramp[:,1],green_ramp[:,1])).T 
		cols=np.append(np.append(np.append(red_ramp,green_ramp,axis=0),blue_ramp,axis=0),grey_ramp,axis=0)
		cols=np.append([[0,255,255],[255,0,255],[255,255,0]],cols,axis=0)
		return cols
	
	def read_rgb_from_ti1(self,file_name):
		"""
			Reads RGB values from a file generated by targen (Argyll CMS package)
			Created e.g by targen -v -d 3 testPatches
			Keeps only the RGB values and rescales them between 0-255

			Inputs:
			file_name: The mane of the *.ti1 file

			Outputs:
			cols: 		A numpy array with the rgb values of a patch in each row
		"""

		file = open(file_name, 'r')
		lines = file.readlines()
		file.close()
		rgb=[]
		for line in lines:
			if line[0].isdigit():
				tmp=line.split()
				rgb.append(tmp[1:4])

		return np.round(np.array(rgb, dtype='float')/100*255)

	def make_rectangle(self):
		"""
		Makes a figure to show the colored rectangles for measurements
		Requires interactive plotting in a figure that can be moved to the place where we want to measure. Likely requires Ipython for that.

		This function takes no input and return nothing. The figure and axis i handled internallt.
		"""
		
		self.fig, self.ax = plt.subplots()
		self.fig.set_facecolor([0,0,0]) #fgure background to black
		self.ax.set_facecolor([0,0,0]) #axis background to black
		self.ax.axis('off')
		rectangle=plt.Rectangle((0,0),1,1,facecolor=[1,1,1])
		self.ax.add_patch(rectangle)
		plt.draw()
		plt.pause(1)
	
	def set_rectangle_color(self, color):
		"""
		Set the color of the rectangle in a figure.

		Inputs:
		color:  The rectangle color. A triple with falues between 0...255

		"""
		
		self.ax.clear()
		self.ax.set_facecolor([0,0,0])
		self.rectangle=plt.Rectangle((0,0),1,1,facecolor=color/255)
		self.ax.add_patch(self.rectangle)
		plt.draw()
		plt.pause(1)

