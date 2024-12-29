import numpy as np
import time

def read_pr650_measurement_from_file(file_name):
	"""
	Read a pr650 measurement text file produced with measure.py
	The file is expected to have in each line a set of measurements in the order
	'colors''XYZ''x_y''u_v''temp_deviation''quality_unit''intensity''spectral_i'
	The indices in the row are defined in the dicitionary 'indices' in the pr650
	class. All values are written with space as separator and newline separating
	measurements.  

	Input: 
	file_name: The name of the text file
 
	Output:
	data:		The rgb and measured data in a numpy array 
	"""

	return np.loadtxt(file_name)

def prepare_data_for_ti3(data):
	"""
	Prepare data from a pr650 measuremnt array for a writing a ti3 file.
	This simply extracts the rgb and XYZ data from each line and does some 
	normalizations.

	Inputs:
	data: 	numpy array of rgb data and corresponding measurements. RGB is 
			expected in the first three columns, then three columns holding 
			the XYZ data.  
	"""
	#Normalize RGB values to the range 0.0-100.0
	rgb_data=data[:,0:3]/255*100
	#Normalize XYZ values to Y=100.0 for white
	#Find the white entry 
	idx=np.where((data[:,0:3]==np.array([255, 255, 255])).all( axis=1))
	xyz_data=data[:,3:6]/np.mean(data[idx,4])*100
	#append RGB and XYZ data
	rgbxyz_data=np.append(rgb_data, xyz_data, axis=1) 
	return rgbxyz_data 


def create_ti3_file(data_array, output_file):
	"""
	Creates a .ti3 file from a NumPy array containing RGB and XYZ data.

	Input:
        data_array (np.ndarray): A NumPy array with rows in the format [R, G, B, X, Y, Z].
        output_file (str): Path to save the .ti3 file.
    """
	# Ensure the array has the correct shape
	if data_array.shape[1] != 6:
		raise ValueError("Input data array must have 6 columns (RGB and XYZ).")

    # Prepare the header
	header = """CTI3

DEVICE_CLASS DISPLAY
NORMALIZED_TO_Y_100 YES
COLOR_REP "RGB_XYZ"
"""
	header +=f"DESCRIPTOR {output_file}\n"
	header +="ORIGINATOR create_ti3_file\n"
	datetime = time.strftime("%Y-%M-%d %H:%M:%S")
	header +=f"CREATED {datetime}\n\n"
	header +="""NUMBER_OF_FIELDS 6
BEGIN_DATA_FORMAT
RGB_R RGB_G RGB_B XYZ_X XYZ_Y XYZ_Z
END_DATA_FORMAT
"""

	# Number of data rows
	num_sets = data_array.shape[0]

	# Add the NUMBER_OF_SETS line
	header += f"NUMBER_OF_SETS {num_sets}\nBEGIN_DATA\n"

	# Prepare the data rows
	data_lines = "\n".join(
		f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f} {row[3]:.6f} {row[4]:.6f} {row[5]:.6f}"
		for row in data_array
    )

	# Add the footer
	footer = "\nEND_DATA\n"

	# Combine all parts
	ti3_data = header + data_lines + footer

	# Save to file
	with open(output_file, "w") as file:
		file.write(ti3_data)

	print(f".ti3 file successfully created: {output_file}")

def create_ti3_from_measurement_file(data_file, output_file):
	"""
	Implements the steps to create and save a .ti3 file from a text file of 
	measurments.

	Inputs:
	input_file:	The name of a text file that reulted from a pr650 measurment
	output_file: The name of the ti3 file to save.
	"""
	data_measured = read_pr650_measurement_from_file(data_file)
	data_ti3 = prepare_data_for_ti3(data_measured)
	create_ti3_file(data_ti3, output_file)

