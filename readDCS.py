
import matplotlib.pyplot as plt
import numpy as np


IMAGE = 'image13.bin'
def main():
	readDCSimage(IMAGE)

def readSingleImage(img):
	with open(img, 'r') as file:
		data = np.fromfile(file, dtype=np.uint16)
		dcsData = data.reshape(320,240,1, order='F')
		fig = plt.figure()

		image = dcsData[:,:,0]
		fig.add_subplot(1,1,1)
		plt.imshow(image)
		plt.savefig('dcs.png')

if __name__ == '__main__':
	main()