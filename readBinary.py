
from PIL import ImageTk,Image 
import os
import numpy as np
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
import tofAnalysis

def readBinaryFile(filepath):
	numBytes = os.path.getsize(filepath)	#size in bytes
	numPixels = int(numBytes/2)
	numFrames = int(numPixels/(320*240))
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

def readDCSimage(img, freq):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,4, order='F')

		#DCS figure
		dcsFig = plt.figure(figsize=(7.5,5.625), dpi=80, bbox_inches='tight',pad_inches = 0)
		for i in range(0,4):
			image = dcsData[:,:,i]
			rotatedImg = np.rot90(image, 1)
			dcsFig.add_subplot(2,2,i+1)
			plt.axis('off')
			plt.imshow(rotatedImg)

		#depth image figure
		heatmap = tofAnalysis.analyze(dcsData, freq)
		rotatedHeatMap = np.rot90(heatmap, 1)
		heatFig = plt.figure(figsize=(7.5,5.625), bbox_inches='tight',pad_inches = 0)
		plt.imshow(rotatedHeatMap)
		plt.axis('off')
	return dcsFig, heatFig

def readSingleImage(img):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,1, order='F')
		fig = plt.figure()

		image = dcsData[:,:,0]
		fig.add_subplot(1,1,1)
		plt.imshow(image)
		plt.savefig('singleImage.png')
        
if __name__ == '__main__':
    print("hi")
    readDCSimage('DCS08.bin', 6)


