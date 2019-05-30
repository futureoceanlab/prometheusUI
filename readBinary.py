import sys

def readBinaryFile(filepath):
	numBytes = os.path.getsize(filepath)	#size in bytes
	numPixels = int(numBytes/2)
	numFrames = int(numPixels/(320*240))
	numBytesPerFrame = int((numPixels/numFrames))
	file = open(filepath, 'r')
	array = np.fromfile(file, dtype=np.uint16)
	for i in range(0,numFrames):
		newArray = array[i*numBytesPerFrame:(i+1)*numBytesPerFrame].reshape(320,240)
		img = Image.fromarray(newArray, mode='L')
		img.save("./generatedImages/newImage"+str(i)+".jpg", 'JPEG')

if __name__ == '__main__':
	readBinaryFile(sys.argv[1])