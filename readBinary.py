
from PIL import ImageTk,Image 
import os
import numpy as np
import sys

def readBinaryFile(filepath):
	numBytes = os.path.getsize(filepath)	#size in bytes
	numPixels = int(numBytes/2)
	numFrames = int(numPixels/(320*240))
	numPixelsPerFrame = int((numPixels/numFrames))
	file = open(filepath, 'r')
	fname = os.path.basename(filepath).split('.')[0]
	array = np.fromfile(file, dtype=np.uint16) - 2048
	for i in range(0,numFrames):
		newArray = array[i*numPixelsPerFrame:(i+1)*numPixelsPerFrame].reshape(320,240)
		img = Image.fromarray(newArray, mode='L')
		img.save("./generatedImages/"+fname+"_"+str(i)+".jpg", 'JPEG')

if __name__ == '__main__':
	#readBinaryFile(sys.argv[1])
    readBinaryFile(sys.argv[1])
