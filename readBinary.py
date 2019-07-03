
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
	if numBytes == 0:
		return filepath
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
		img_name = "./images/" + fname + "_" + str(i) + ".jpg"
		img.save(img_name, 'JPEG')
		img_names.append(img_name)
	return img_names

def getDCSFigures(img, freq):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,4, order='F')

		dcsFig = plt.figure(figsize=(7.5,5.625), dpi=80)
	
		#3d
		#DCS figure
		for i in range(0,4):
			image = dcsData[:,:,i]
			if img.split('.bin')[0][-1] == '0':
				rotatedImg = np.rot90(image, 3)
			else:
				rotatedIMg = np.rot90(image, 1)
			dcsFig.add_subplot(2,2,i+1)
			plt.axis('off')
			plt.imshow(rotatedImg)
		dcsFig.tight_layout()

		#depth image figure
		heatmap = tofAnalysis.analyze(dcsData, freq)
		if img.split('.bin')[0][-1] == '0':
			rotatedHeatMap = np.rot90(heatmap, 3)
		else:
			rotatedHeatMap = np.rot90(heatmap, 1)
		heatFig = plt.figure(figsize=(7.5,5.625), dpi=80)
		# heatFig.tight_layout()
		plt.imshow(rotatedHeatMap)
		plt.axis('off')
	return dcsFig, heatFig

def get_4DCS_PNG(img):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)

		if '_2D_' in img: 
			return 'noDCS.jpg'
			# return read_2D_BINImage(img)
		dcsData = data.reshape(320,240,4, order='F')

		dcsFig = plt.figure(figsize=(7.5,5.625), dpi=80)
	
		#DCS figure
		for i in range(0,4):
			image = dcsData[:,:,i]
			if img.split('.bin')[0][-1] == '0':
				rotatedImg = np.rot90(image, 3)
			else:
				rotatedIMg = np.rot90(image, 1)
			dcsFig.add_subplot(2,2,i+1)
			plt.axis('off')
			plt.imshow(rotatedImg)
		dcsFig.tight_layout()
		outputFileName = img.replace('.bin', '_4DCS.png')
		plt.savefig(outputFileName)
		plt.clf()
		# plt.close()
	return outputFileName

def read_3D_BINimage(img, freq):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,4, order='F')

		#depth image figure
		heatmap = tofAnalysis.analyze(dcsData, freq)
		heatFig = plt.figure(figsize=(7.5,5.625), dpi=80)
		if img.split('.bin')[0][-1] == '0':
			plt.imshow(np.rot90(heatmap, 3))
		else:
			plt.imshow(np.rot90(heatmap, 1))
		plt.axis('off')
		
		outputFileName = img.replace('.bin', '_depth.png')
		# outputFileName = './images/'+outputFileName

		plt.savefig(outputFileName)
		plt.clf()
		# plt.close()
	return outputFileName

def read_2D_BINImage(img):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,1, order='F')
		fig = plt.figure()

		image = dcsData[:,:,0]
		if img.split('.bin')[0][-1] == '0':
			plt.imshow(np.rot90(image, 3))
		else:
			plt.imshow(np.rot90(image, 1))

		plt.axis('off')
		outputFileName = img.replace('.bin', '_depth.png')
		# outputFileName = './images/'+outputFileName
		plt.savefig(outputFileName)
		plt.clf()
		# plt.close()
	return outputFileName

def convertBINtoPNG(binPath, freq):
	try:
		if os.stat(binPath).st_size == 0:
			raise Exception("empty file {}".format(binPath))
		with open(binPath, 'r') as file:
			if '_2D_' in binPath:
				return read_2D_BINImage(binPath)
			else:
				return read_3D_BINimage(binPath, freq)
	except OSError:
		raise Exception("Invalid path {}".format(binPath))
	

        
if __name__ == '__main__':
    print("hi")
    convertBINtoPNG('_3D_.bin', 6)


