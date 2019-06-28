import math
import numpy as np


def analyze(dcsData):

	result = list(map(lambda w,x,y,z: dcdInverse(w,x,y,z), dcsData[:,:,0], dcsData[:,:,1], dcsData[:,:,2], dcsData[:,:,3]))
	print("RESULT: ", result)
	return np.array(result).reshape(320,240, order='F')

def dcsInverse(dcs0, dcs1, dcs2=None, dcs3=None):

	normDCIconv = []
	normDCIconvshift = []


	if dcs2 != None and dcs3 != None:
		dcs0 -= dcs2
		dcs1 -= dcs3

	amplitude = float(abs(dcs0) + abs(dcs1))

	if math.isnan(dcs0) or math.isnan(dcs1):
		quality = 'NaN'
		phase = -1

	elif dcs0 == dcs1 == 0:
		phase = -1
		quality = 0

	else:
		quality = math.sqrt(dcs0**2 + dcs1**2)
		normDCS0 = dcs0/amplitude
		normDCS1 = dcs1/amplitude

		if normDCS0 >= max(normDCIconv):
			#find the rising index
			part1 = filter(lambda x: x <= normDCS1, normDCIconvshift[:len(normDCIconvshift)-1])
			part2 = filter(lambda x: x > normDCS1, normDCIconvshift[1:])
			riseIndex = list(set(part1) & set(part2))[0]

			#use it to find the slope
			slope = float(normDCIconvshift[riseIndex] - normDCIconvshift[riseIndex-1])

			est = (normDCS1 - normDCIconvshift[riseIndex])/slope

			#find the phase
			assert(type(wavelength) == float)
			phase = ((riseIndex + est)/wavelength)%1.0

		elif normDCS0 <= min(normDCIconv):

			part1 = filter(lambda x: x >= normDCS1, normDCIconvshift[:len(normDCIconvshift)-1])
			part2 = filter(lambda x: x < normDCS1, normDCIconvshift[1:])
			fallIndex = list(set(part1) & set(part2))[0]

			slope = float(normDCIconvshift[fallIndex] - normDCIconvshift[fallIndex-1])

			est = (normDCS1 - normDCIconvshift[fallIndex])/slope

			#find the phase
			assert(type(wavelength) == float)
			phase = ((riseIndex + est)/wavelength)%1.0

		else:
			part1 = filter(lambda x: x <= normDCS0, normDCIconv[:len(normDCIconv)-1])
			part2 = filter(lambda x: x > normDCS0, normDCIconv[1:])
			riseIndex = list(set(part1) & set(part2))[0]

			part1 = filter(lambda x: x >= normDCS0, normDCIconv[:len(normDCIconv)-1])
			part2 = filter(lambda x: x < normDCS0, normDCIconv[1:])
			fallIndex = list(set(part1) & set(part2))[0]

			if ((normDCS1 > min(normDCIconvshift[riseIndex], normDCIconvshift[riseIndex+1])) and (normDCS1 > max(normDCIconvshift[riseIndex], normDCIconvshift[riseIndex+1]))) or normDCS1 <= min(normDCIconvshift):
				section = [riseIndex, riseIndex+1]
			else:
				section = [fallIndex, fallIndex+1]

			slope = normDCIconv[section[1]] - normDCIconv[section[0]]
			est = (normDCS0 - normDCIconv[section[0]])/slope

			assert(type(wavelength) == float)
			phase = ((section[0] + est)/wavelength)%1.0
	
	print("PHASE: ", phase)
	return phase