#!?usr/bin/env python3

import os
import sys
import time
import select

import uiFunctionCalls

def timelapse(photoDir, photoDim):
	while True:
		fileName = str(datetime.utcnow().strftime("%m%d%H%M%S.%f")) + photoDim
		fileLocation = os.path.join(photoDir, fileName)
		if photoDim == "_2D_":
			returnedFiles = uiFunctionCalls.capturePhotoCommand2D(fileLocation)
		else:
			returnedFiles = uiFunctionCalls.capturePhotoCommand3D(fileLocation)
		# line = sys.stdin.readline()
		# if line:
		# 	print(line)
		# 	break
		if select.select([sys.stdin,],[],[],0.0)[0]:
			# parent communicated end of timelapse
			print("Bye!")
		    break
		time.sleep(.05)



if __name__=="__main__":
	photoDir = sys.argv[1]
	photoDim = sys.argv[2]
	timelapse(photoDir, photoDim)