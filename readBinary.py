
from PIL import ImageTk,Image 
import os
import numpy as np
import sys

def readBinaryFile(filepath):
	print(filepath)
	numBytes = os.path.getsize(filepath)	#size in bytes
	print(numBytes)
	numPixels = int(numBytes/2)
	print(numPixels)
	numFrames = int(numPixels/(320*240))
	print(numFrames)
	numPixelsPerFrame = int((numPixels/numFrames))
	file = open(filepath, 'r')
	fname = os.path.basename(filepath).split('.')[0]
	array = np.fromfile(file, dtype=np.uint16) - 2048
	img_names = []
	for i in range(0,numFrames):
		newArray = array[i*numPixelsPerFrame:(i+1)*numPixelsPerFrame].reshape(320,240)
		img = Image.fromarray(newArray, mode='L')
		img_name = "./generatedImages/" + fname + "_" + str(i) + ".jpg"
		img.save(img_name, 'JPEG')
		img_names.append(img_name)
	return img_names

if __name__ == '__main__':
	#readBinaryFile(sys.argv[1])
    readBinaryFile(sys.argv[1])
