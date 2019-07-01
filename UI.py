#!/usr/bin/env python3

# Author: Evan Denmark
# Prometheus UI
# June 27, 2019

import tkinter as tk
from tkinter.ttk import Frame, Button, Label, Style 
from tkinter import *
from PIL import ImageTk,Image 
import gpiozero as gpio
import time
import os
import numpy as np
import uiFunctionCalls
import camera_power
import configure_camera as camera_configure
from datetime import datetime
import csv
from random import randint
import i2c_functions as i2c
import readBinary
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import prom_GPIO as pg
import time

SCREEEN_WIDTH = 1080
BUTTON_LONGPRESS_TIME = 1
EXPOSURE_OPTIONS = [30, 100, 300, 1000, 3000]
PI_DELAY_OPTIONS = [0,1]
MOD_FREQ_OPTIONS = [0,1]
NUM_EXPOSURES = len(EXPOSURE_OPTIONS)
MODE_OPTIONS = ["CAPTURE", "MENU"]
CAPTURE_MODE_DISPLAYS = ["DCS IMAGES", "POINT CLOUD", "RICH DATA", "COLOR MAP", "PREVIOUS IMAGES", "LIVE", ""]
HDR_SETTINGS = {0:[[1],[30,100,300,1000,3000],[0],[0]],
			    1:[[1],[300],[0],[0,1]],
			    2:[[0,1],[30,100,300,1000,3000],[0,1],[0,1]]}
			    # setting 0: an exposure test
			    #         1: mod freq test
			    #         2: entire blast
MENUTREE = {'root':{
							'Camera Settings': {'CamSubsetting1': 'f22',
												'CamSubsetting2': '1/250',
												'CamSubsetting3': 800
												},
							'Physical Settings':{'PhysicalSetting1':1,
												 'PhysicalSetting2':2,
												 'PhysicalSetting3':3
												} , 
							'Light Settings':{ 'lightSetting1': 4,
												'lightSetting2': 5,
												'lightSetting3': 6
											}

							}
						}

TEMP_MENUTREE ={'root': {
						"DIMENSION MODE" : ('2D'  , ['2D','3D']),
						"MODULATION FREQ": (0     , [0,1]),
						"ENABLE PI DELAY": (0     , [0,1]),
						"CLOCK":		   ('EXT' , ['EXT','INT']),
						"CLOCK FREQ"	 : ('6 Hz', ['6 Hz', '12 Hz', '24 Hz']),
						"_RESTART BBB_"  : (' '   , [' ','restarting']),
						"_SHUTDOWN BBB_" : (' '   , [' ','BYE!']), 
						"HDR SETTING"    : (0     , ['EXPOSURE','MOD FREQ','BLAST'])

}
	
}


class MenuTree():
	# A tree is a list of nodes 
	# Nodes have a name and a list of child nodes
	# The purpose of the tree is to make it easy to get
	# the previous and next level of the menu

	def __init__(self, treeStructure):
		#treeStructure is a dictionary, like the MENU_TREE above

		self.root = 'root'
		self.tree = self.makeTree(treeStructure)
		self.currentLevel = self.tree

	def makeTree(self, treeStructure):
		#recursively make each TreeNode be a name a list of child TreeNodes

		if type(treeStructure) is not dict:
			return treeStructure
		treeFromHere = []
		for key in treeStructure:
			treeFromHere.append(TreeNode(key, self.makeTree(treeStructure[key])) )
			
		return treeFromHere

	def getSelectionLevel(self, selection):
		return selection.getImmediateChildren()

	def traverseDownToSelectionLevel(self, selection):
		#when the user clicks on the selection, this gets the children of that selection
		self.currentLevel = self.getSelectionLevel(selection)

	def goUpLevel(self, currentListOfNodes):
		self.currentLevel = self.findPreviousLevel()

	def printCurrentLevel(self):
		for i in self.currentLevel:
			print("  Node: ", i.name)

	def printGivenLevel(self, given):
		for n in given:
			print(n.name)

	def isAtRoot(self):
		return self.tree[0].getImmediateChildren() == self.currentLevel

	def isAtTempRoot(self):
		#TEMP
		return True

	def findPreviousLevel(self):
		exploreList = [self.tree[:]]
		if self.currentLevel == self.tree:
			return self.tree
		while True:
			tempExploreList = []
			for nodeList in exploreList:
				for node in nodeList:
					nodeChildren = node.getImmediateChildren()
					if set(self.currentLevel) == set(nodeChildren):
						return exploreList[0]
					tempExploreList.append(nodeChildren)
				exploreList = tempExploreList[:]


class TreeNode():
	def __init__(self, name, childrenOrValue):
		self.name = name

		if type(childrenOrValue)==list:
			#a node has children
			self.children = sorted(childrenOrValue, key=lambda x: x.name)
			self.value = None
		else:
			#or it is a leaf
			self.value = childrenOrValue
			self.children = None

	def getImmediateChildren(self):
		return self.children

	def sortLevel(self,children):        
		for i in range(len(children)):
			minimum = i
			
			for j in range(i + 1, len(children)):
				# Select the smallest value
				if children[j].name < children[minimum].name:
					minimum = j

			# Place it at the front of the 
			# sorted end of the array
			children[minimum], children[i] = children[i], children[minimum]
				
		return children

	def isLeaf(self):
		return self.children == None

	def getValue(self):
		return self.value

	def changeValue(self, newVal):
		if self.value:
			self.value = newVal

	def printChildren(self):
		s = ''
		for c in self.getImmediateChildren():
			s += c.name+' '
		print(s)


class Application(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		self.master = master

		self.exposure2d = 1000
		self.exposure3d = 1000
		self.title = "CAPTURE"
		self.modFreq = 0 
		self.piDelay = 0 
		self.enableCapture = 0 
		self.HDRmode = 0		#is HDR enabled
		self.HDRTestSetting = 0	#when taking HDR, what test should we run? see HDR_SETTINGS - the key to dictionary
		self.clockSource = 1	#0 internal; 1 external
		self.setClock(self.clockSource)
		self.clockFreq = 6
		
		#states
		self.isTakingVideo = False
		self.showingLiveView = False
		self.mode = 0       #   0 is capture; 1 is menu
		self.display = 0    
		# DISPLAY INDEXES
		# There are 4 main displays in capture mode (0,1,2,3)
		# The additional displays are viewing the previous image and live view
		# The four main displays rotate through by single clicks
		# The two extra displays can be accessed at any time through long clicks
		# 0  --  4x DCS images  
		# 1  --  point cloud
		# 2  --  'rich data' - state of the system
		# 3  --  color map image
		# 4  --  previous image
		# 5  -- live view 
		# -1 --  menu display

		#previous image settings
		self.viewingPreviousImages = False
		self.previousImages = []
		self.numPreviousImages = 0
		self.createMainCSV()	
		# self.previousImages = ['DCS08_3D_.bin', 'DCS09_3D_.bin','DCS10_3D_.bin','image13_2D_.bin'] #TEMPORARY OVERRIDE OF PREVIOUS IMAGES
		self.currentPreviousImage = max(0, len(self.previousImages)-1)
		self.dimensionMode = 0

		#frame areas of the UI
		self.topArea = None
		self.mainArea = None
		self.dataArea = None
		self.menuFrame = None
		self.fullScreen = True

		#data contained in the UI 
		self.mainImportantData = {'Battery': '50%', 'Mem': str(43.2)+'GB', 'S/N ratio': 0.6, 'EXP 2D':self.exposure2d, 'EXP 3D': self.exposure3d, 'VIDEO':"NO"} 
		self.richData = {'EXP 2D':self.exposure2d, 'EXP 3D': self.exposure3d}
		self.menu_tree = MenuTree(MENUTREE)
		self.temp_menu_tree = MenuTree(TEMP_MENUTREE)
		self.previousImage = 'ocean.jpg'
		self.currentSelectionButton = None
		self.currentSelectionNode = None
		self.nodeToButtonDict = {}
		self.I2Cdata = {'direction': None, 'temperature': None, 'pressure':None}
		self.currentLogFile = ""

		#button information
		self.MENU_BTN = gpio.Button(pg.menuGPIO(), pull_up=True)
		self.DISP_BTN = gpio.Button(pg.dispGPIO(), pull_up=True)
		# self.EXPO_BTN = gpio.Button(pg.expoGPIO(), pull_up=True)
		self.ACTN_BTN = gpio.Button(pg.actnGPIO(), pull_up=True)
		# self.HDR_BTN =  gpio.Button(pg.hdrGPIO(), pull_up=True)
		self.MENU_BTN.when_pressed = self.MENU_pressed
		# self.HDR_BTN.when_pressed  = self.HDR_pressed


		self.JS1_MENU_BTN = gpio.Button(pg.js1_menuGPIO())
		self.JS1_DISP_BTN = gpio.Button(pg.js1_dispGPIO())
		self.JS1_EXPO_BTN = gpio.Button(pg.js1_expoGPIO())
		self.JS1_ACTN_BTN = gpio.Button(pg.js1_actnGPIO())
		self.JS1_HDR_BTN  = gpio.Button(pg.js1_hdrGPIO())

		self.JS1_MENU_BTN.when_pressed = self.MENU_pressed
		self.JS1_HDR_BTN.when_pressed = self.HDR_pressed

		self.JS2_MENU_BTN = gpio.Button(pg.js2_menuGPIO())
		self.JS2_DISP_BTN = gpio.Button(pg.js2_dispGPIO())
		self.JS2_EXPO_BTN = gpio.Button(pg.js2_expoGPIO())
		self.JS2_ACTN_BTN = gpio.Button(pg.js2_actnGPIO())
		self.JS2_HDR_BTN  = gpio.Button(pg.js2_hdrGPIO())

		self.JS2_MENU_BTN.when_pressed = self.MENU_pressed
		self.JS2_HDR_BTN.when_pressed = self.HDR_pressed

		self.dispBtnState = 0
		self.expoBtnState = 0
		self.actnBtnState = 0
		self.dispHeldStart = 0
		self.expoHeldStart = 0
		self.actnHeldStart = 0
		self.dispSinceLongheld = 0 
		self.expoSinceLongheld = 0
		self.actnSinceLongheld = 0 
		self.buttonColor = 'white'

		#create the initial UI
		self.createMainLog()
		master.geometry("{0}x{1}+0+0".format(master.winfo_screenwidth(), master.winfo_screenheight()))
		master.bind('<Escape>',lambda e: self.toggleFullScreen())
		master.bind('q', lambda x: master.quit())
		self.create_layout()

		#setters for prom-cli
		camera_configure.configure_camera(0)
		camera_configure.configure_camera(1)

		self.set_exposure(0, self.exposure2d)
		self.set_exposure(1, self.exposure3d)


	def toggleFullScreen(self):
		self.fullScreen = not self.fullScreen
		self.master.attributes('-fullscreen', self.fullScreen)

	def nonRecursiveButtonCheck(self):
		# The function that continuously checks the state of the buttons

		#MENU BUTTON is just short press so it is handled in __init__

		# DISPLAY BUTTON
		if (time.time() - self.dispSinceLongheld)>1:
			if (self.DISP_BTN.is_pressed or self.JS1_DISP_BTN.is_pressed or self.JS2_DISP_BTN.is_pressed) and not self.dispBtnState:
				#button is being pressed down 
				self.dispBtnState = 1
				self.dispHeldStart = time.time()

			if not (self.DISP_BTN.is_pressed or self.JS1_DISP_BTN.is_pressed or self.JS2_DISP_BTN.is_pressed) and self.dispBtnState:
				#button is being released
				self.dispBtnState = 0
				lengthOfPress = time.time() - self.dispHeldStart 
				if lengthOfPress < BUTTON_LONGPRESS_TIME:
					#it was a short press
					self.DISP_short_pressed()

			if self.dispBtnState:
				#check if it is longpress yet
				lengthOfPress = time.time() - self.dispHeldStart
				if lengthOfPress > BUTTON_LONGPRESS_TIME:
					#long press
					self.dispBtnState = 0
					self.dispSinceLongheld = time.time()
					self.DISP_long_pressed()


		# EXPOSURE BUTTON
		if (time.time() - self.expoSinceLongheld)>1:
			if (self.JS1_EXPO_BTN.is_pressed or self.JS2_EXPO_BTN.is_pressed) and not self.expoBtnState:
				#button is being pressed down 
				self.expoBtnState = 1
				self.expoHeldStart = time.time()

			if not (self.JS1_EXPO_BTN.is_pressed or self.JS2_EXPO_BTN.is_pressed) and self.expoBtnState:
				#button is being released
				self.expoBtnState = 0
				lengthOfPress = time.time() - self.expoHeldStart 
				if lengthOfPress < BUTTON_LONGPRESS_TIME:
					#it was a short press
					self.EXP_short_pressed()

			if self.expoBtnState:
				#check if it is longpress yet
				lengthOfPress = time.time() - self.expoHeldStart
				if lengthOfPress > BUTTON_LONGPRESS_TIME:
					#long press
					self.expoBtnState = 0
					self.expoSinceLongheld = time.time()
					self.EXP_long_pressed()


		#ACTION BUTTON
		if (time.time() - self.actnSinceLongheld)>1:
			if (self.ACTN_BTN.is_pressed or self.JS1_ACTN_BTN.is_pressed or self.JS2_ACTN_BTN.is_pressed) and not self.actnBtnState:
				#button is being pressed down 
				self.actnBtnState = 1
				self.actnHeldStart = time.time()

			if not (self.ACTN_BTN.is_pressed or self.JS1_ACTN_BTN.is_pressed or self.JS2_ACTN_BTN.is_pressed) and self.actnBtnState:
				#button is being released
				self.actnBtnState = 0
				lengthOfPress = time.time() - self.actnHeldStart 
				if lengthOfPress < BUTTON_LONGPRESS_TIME:
					#it was a short press
					self.ACTN_short_pressed()

			if self.actnBtnState:
				#check if it is longpress yet
				lengthOfPress = time.time() - self.actnHeldStart
				if lengthOfPress > BUTTON_LONGPRESS_TIME:
					#long press
					self.actnBtnState = 0
					self.actnSinceLongheld = time.time()
					self.ACTN_long_pressed()
	

	def buttonCheck(self):
		# The function that continuously checks the state of the buttons

		self.nonRecursiveButtonCheck()

		# This allows for the button checker to run continously, 
		# alongside the mainloop
		self.master.after(1, self.buttonCheck)

	def checkBeagle(self):
		camera_power.connect_both_cameras()
		#camera_power.turn_on_BBBx(0)
		#camera_power.turn_on_BBBx(1)
		self.master.after(10000, self.buttonCheck)

	def createMainLog(self):
		numFolders, numFiles = self.directoryCounter("./logs")
		newFile = open("./logs/"+"log_"+str(numFiles)+".txt", "w+")
		newFile.write("START TIME: "+str(datetime.utcnow().strftime("%m%d%H%M%S")))
		newFile.close()
		self.currentLogFile = newFile.name

	def updateMainLog(self, msg):
		logFile = open(self.currentLogFile, 'a')
		logFile.write(msg+'\n')
		logFile.close()

	def createMainCSV(self):
		#on startup, check if the main csv exists
		#if it does, populate the previous images
		#otherwise, create a new one
		self.currentCSVFile = "./mainCSV.csv"
		try:
			file = open(self.currentCSVFile, 'r')
			reader = csv.reader(file, delimiter=',')
			for row in reader:
				self.previousImages.append(row[1])	#appending the image file location
				self.numPreviousImages +=1
				#the most recent previous image is at the end
		except FileNotFoundError:
			file = open(self.currentCSVFile, "w")
			self.previousImages = []
			self.numPreviousImages = 0
		file.close()

	def get_mode(self):
		return self.mode

	def get_display(self):
		return self.display

	def get_exposure2d(self):
		return self.exposure2d

	def get_exposure3d(self):
		return self.exposure3d

	def get_title(self):
		return MODE_OPTIONS[self.mode] +  '  -  ' + CAPTURE_MODE_DISPLAYS[self.get_display()]

	def get_mainImportantData(self):
		return self.mainImportantData

	def get_video_state(self):
		return self.isTakingVideo

	def get_live_view_state():
		return self.showingLiveView

	def get_previousImage(self, x):
		prevImagePath = self.previousImages[x%len(self.previousImages)]
		return Image.open(self.previousImages[x%len(self.previousImages)])

	def get_previousImage_BIN(self, x):
		if len(self.previousImages) > 0:
			binPath = self.previousImages[x%len(self.previousImages)]
			print("getting bin; ", binPath)
			pngPath = readBinary.convertBINtoPNG(binPath, self.clockFreq)
		else: 
			pngPath = 'noPrevImg.jpg'
		print("PNG PATH: ", pngPath)
		return Image.open(pngPath)

	def get_previousFigure(self, x):
		prevImagePath = self.previousImages[x%len(self.previousImages)]
		dcsFig, heatFig = readBinary.getDCSFigures(prevImagePath, self.clockFreq)
		return heatFig

	def get_previousImageIndex(self, offset=0):
		return (self.currentPreviousImage+offset)%len(self.previousImages)

	def get_PC_image(self):
		return ImageTk.PhotoImage(Image.open('whale.jpg').resize((1440,950),Image.ANTIALIAS))
		# return ImageTk.PhotoImage((self.get_previousImage(self.get_previousImageIndex())).resize((600,450),Image.ANTIALIAS))

	def get_colorMap_image(self):
		return ImageTk.PhotoImage(Image.open('whale.jpg').resize((1440,950),Image.ANTIALIAS))
		# return ImageTk.PhotoImage((self.get_previousImage(self.get_previousImageIndex())).resize((800,480),Image.ANTIALIAS))

	def get_live_image(self, path):
		return ImageTk.PhotoImage(Image.open(path).resize((1440,950),Image.ANTIALIAS))

	def get_live_image_temp(self, x):
		if x%2==0:
			img = Image.open('small1.jpg').resize((1440,950),Image.ANTIALIAS)
		else:
			img = Image.open('small2.jpg').resize((1440,950),Image.ANTIALIAS)
		return ImageTk.PhotoImage(img)
		
	def get_richData_string(self):
		s = ''
		for key in self.richData:
			s += key+' : '+str(self.richData[key])+'\n'
		return s

	def get_mainImportantData_string(self):
		s = ''
		for key in self.mainImportantData:
			s += key+' : '+str(self.mainImportantData[key])+'\n'
		return s

	def update_data(self,dictionary,key,val):
		dictionary[key] = val

	def toggle_live_view(self):
		self.showingLiveView = not self.showingLiveView
		if self.display == 5:
			self.display = 0
		else:
			self.display = 5

	def set_live_view(self, x):
		self.showingLiveView = x

	def toggle_prev_image(self):
		self.viewingPreviousImages = not self.viewingPreviousImages
		if self.display == 4:
			self.display = 0
		else:
			self.display = 4

	def toggle_video_state(self):
		self.isTakingVideo = not self.isTakingVideo

	def set_video_state(self, x):
		self.isTakingVideo = x 

	def update_display(self):
		# function that is called after every button push to update
		# the state of the display

		#update title
		self.topArea["text"] = self.get_title()

		#update data
		self.dataArea['text'] = self.get_mainImportantData_string()

		#the display below is the display that the screen is CHANGING TO
		#not the one that it is coming from
		display = self.get_display()
		if display == 0:
			self.setDCSImage(self.getDCSImage())

		#update main area dimensions
		#erase everything that goes in main area
		self.menuFrame.grid_forget()
		for i in [0,1,2,3,4,5]:
			self.mainArea.winfo_children()[i].pack_forget()

		if display in [-1,2]:
			#erase the data grid
			self.winfo_children()[2].grid_forget()

		#now display things we want
		if display == -1:
			self.mainArea.winfo_children()[-1].grid()
		else:
			self.mainArea.winfo_children()[display].pack(fill=BOTH, expand=YES)

		if display in [0,3,4]:
			self.winfo_children()[2].grid(row=1, column=1,sticky=W+N+E+S)



	def create_layout(self):

		#setting up all of the displays and hiding the ones that are not
		#used at the inital turn on

		self.pack(fill=BOTH, expand=True)
		self.columnconfigure(0,weight=3)
		self.columnconfigure(1,weight=1)
		self.rowconfigure(0,weight=1)
		self.rowconfigure(1,weight=5)

		#the 3 main frames

		topLabel = Label(self, text=self.get_title(), borderwidth=5, font=('Helvetica', 36))
		topLabel.grid(row=0, column=0, sticky=W+N+E+S, columnspan=3, rowspan=1)

		mainFrame = tk.Frame(self, borderwidth=5)
		mainFrame.grid(row=1,column=0, sticky=W+N+E+S)

		dataLabel = Label(self, text=self.get_mainImportantData_string(), relief=RIDGE, font=('Helvetica', 36),  borderwidth=5, justify=LEFT)
		dataLabel.grid(row=1, column=1, sticky=W+N+E+S)

		self.topArea = topLabel
		self.mainArea = mainFrame
		self.dataArea = dataLabel

		#DCS grid -- display = 0
		# dcsFigure, heatFig = readBinary.getDCSFigures(self.previousImages[self.currentPreviousImage], self.clockFreq)
		# canvas = FigureCanvasTkAgg(dcsFigure, mainFrame)
		# canvas.draw()
		# canvas.get_tk_widget().pack()

		dcsCanvas = tk.Canvas(mainFrame, width=800, height=480)
		if not len(self.previousImages):
			fourDCSImages = ImageTk.PhotoImage(Image.open('noDCS.jpg').resize((1440,950),Image.ANTIALIAS))
			mainFrame.fourDCSImages = fourDCSImages
			dcsCanvas.create_image(0,0,anchor=NW, image=fourDCSImages)
		else:
			fourDCSImages = ImageTk.PhotoImage(Image.open(readBinary.get_4DCS_PNG(self.previousImages[self.currentPreviousImage])).resize((1440,950),Image.ANTIALIAS))
			mainFrame.fourDCSImages = fourDCSImages
			dcsCanvas.create_image(0,0,anchor=NW, image=fourDCSImages)
		dcsCanvas.pack(fill=BOTH, expand=YES)

		#Point Cloud -- display = 1
		pointCloudCanvas = tk.Canvas(mainFrame, width=800, height=600)
		img = self.get_PC_image()
		mainFrame.img = img
		pointCloudCanvas.create_image(0,0,anchor=NW, image=img)
		pointCloudCanvas.pack_forget()

		#Rich Data -- display = 2
		richDataGrid = tk.Frame(mainFrame)
		rowNum = 0 
		for key in self.richData:
			dataRowKey = Label(richDataGrid, text=key,font=('Helvetica', 36))
			dataRowKey.grid(row=rowNum,column=0)
			dataRowVal = Label(richDataGrid, text=str(self.richData[key]),font=('Helvetica', 36) )
			dataRowVal.grid(row=rowNum,column=1)
			rowNum+=1
		richDataGrid.grid_forget()

		# # #Color Map -- display = 3
		# heatCanvas = FigureCanvasTkAgg(heatFig, mainFrame)
		# heatCanvas.draw()
		# heatCanvas.get_tk_widget().pack()
		# heatCanvas.get_tk_widget().pack_forget()

		colorCanvas = tk.Canvas(mainFrame, width=800, height=480)
		print()
		colorImg = ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((1440,950),Image.ANTIALIAS))
		mainFrame.colorImg = colorImg
		colorCanvas.create_image(0,0,anchor=NW, image=colorImg)
		colorCanvas.pack_forget()

		# #PreviousImg -- display = 4
		# prevFigureCanvas = FigureCanvasTkAgg(heatFig, mainFrame)
		# mainFrame.previousFigure = prevFigureCanvas
		# prevFigureCanvas.draw()
		# prevFigureCanvas.get_tk_widget().pack()
		# prevFigureCanvas.get_tk_widget().pack_forget()

		prevImageCanvas = tk.Canvas(mainFrame, width=800, height=480)
		prevImg1 = ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((720,425),Image.ANTIALIAS))
		prevImg2 = ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage-1).resize((720,425),Image.ANTIALIAS))
		mainFrame.prevImg1 = prevImg1
		mainFrame.prevImg2 = prevImg2
		prevImageCanvas.create_image(0,0,anchor=NW, image=prevImg1)
		prevImageCanvas.create_image(100,0, anchor=NW, image=prevImg2)
		prevImageCanvas.pack_forget()



		# prevImgCanvas = tk.Frame(mainFrame, width=800, height=480)
		# prevImg1 = ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((1440,950),Image.ANTIALIAS))
		# prevImg2 = ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage-1).resize((1440,950),Image.ANTIALIAS))

		# mainFrame.prevImgCanvas.prevImg1 = prevImg1
		# mainFrame.prevImgCanvas.prevImg2 = prevImg2
		# prevImgCanvas.create_image(0,0,anchor=NW, image=prevImg1)
		# prevImgCanvas.create_image(400,0,anchor=NW, image=prevImg1)

		# prevImgCanvas.pack_forget()

		# #Live View -- display = 5
		liveViewCanvas = tk.Canvas(mainFrame, width=800, height=480)
		liveImg = self.get_live_image('noLiveViewAvailable.jpg')
		mainFrame.liveImg = liveImg
		liveViewCanvas.create_image(0,0,anchor=NW, image=liveImg)
		liveViewCanvas.pack_forget()


		self.menuFrame = tk.Frame(mainFrame, bg='green')
		labelName = Label(self.menuFrame, text="")
		self.menuFrame.pack()
		# self.menuFrame.rowconfigure(0,weight=1)
		# self.menuFrame.columnconfigure(0,weight=1)
		# self.createMenu(self.menuFrame, self.menu_tree.tree[0], True)
		self.createTempMenu()
		# self.createMenu2(self.menuFrame)

		# self.menuFrame.grid_forget()
		self.menuFrame.pack_forget()


	def createMenu(self, previousMenu, clickedNode, atRoot):

		if not atRoot:
			previousMenu.grid_forget()
		newMenu = tk.Frame(self.menuFrame, bg='red', width=750, height=400)
		level = self.menu_tree.getSelectionLevel(clickedNode)

		self.menu_tree.traverseDownToSelectionLevel(clickedNode)
		rowNumber = 0 
		for child in level:
			if child.isLeaf():
				settingName = Button(previousMenu, text=str('Change ')+child.name)
				settingName.grid(row=rowNumber, column=0)
				settingValue = Label(previousMenu, text=child.value)
				settingValue.grid(row=rowNumber, column=1)
				self.nodeToButtonDict[child] = (settingName, settingValue)
			else:
				settingCategory = Button(previousMenu, text=child.name, command=lambda : self.createMenu(self.menuFrame,child,False))
				settingCategory.grid(row=rowNumber, column=0)
				self.nodeToButtonDict[child] = (settingCategory, None)
			rowNumber +=1


	def createMenu2(self,frame):
		mnu = self.makeMenu(frame)
		mnu.config(bd=2, relief=RAISED)
		frame.pack(expand=YES, fill=BOTH)
		Label(frame, bg='black', height=5, width=15).pack(expand=YES, fill=BOTH)

	def notdone(self):
		return

	def makeMenu(self,parent):
		menubar = Frame(parent)                        
		menubar.pack(side=TOP, fill=X)



		
		button1 = Menubutton(menubar, text='Camera Settings')
		button1.pack(side=LEFT)
		cam = Menu(button1)
		cam.add_command(label='ISO',  command=self.notdone)
		cam.add_command(label='Aperture', command=self.notdone)
		cam.add_command(label='Shutter Speed',    command=parent.quit)
		button1.config(menu=cam)
		 
		button2 = Menubutton(menubar, text='Light Settings')
		button2.pack(side=LEFT)
		lightBtn = Menu(button2, tearoff=0)
		lightBtn.add_command(label='Brightness',     command=self.notdone)
		lightBtn.add_command(label='Speed',   command=self.notdone)
		lightBtn.add_separator()
		button2.config(menu=lightBtn)

		button3 = Menubutton(menubar, text='Physical Settings')
		button3.pack(side=LEFT)
		physBut = Menu(button3, tearoff=0)
		physBut.add_command(label='Position',     command=self.notdone)
		physBut.add_command(label='Focal Length',   command=self.notdone)
		physBut.add_separator()
		button3.config(menu=physBut)
		 
		submenu = Menu(physBut, tearoff=0)
		submenu.add_command(label='Depth', command=parent.quit)
		submenu.add_command(label='Eggs', command=self.notdone)
		physBut.add_cascade(label='More Physical Settings',   menu=submenu)
		return menubar


	def createTempMenu(self):

		level = self.menu_tree.getSelectionLevel(self.temp_menu_tree.tree[0])
		self.menu_tree.traverseDownToSelectionLevel(self.temp_menu_tree.tree[0])
		rowNumber = 0
		for child in level: 

			
			settingValue = Label(self.menuFrame, text=child.value[0], font=('Helvetica', 48))
			settingValue.grid(row=rowNumber, column=1,  sticky=W+N+E+S)
			settingKey = Button(self.menuFrame, text=child.name, font=('Helvetica', 48), command=lambda: self.changeMenuValue(child, settingValue))
			self.buttonColor = settingKey.cget('bg')
			settingKey.grid(row=rowNumber, column=0,  sticky=W+N+E+S)
			self.nodeToButtonDict[child] = (settingKey, settingValue)
			if rowNumber == 0:
				self.currentSelectionButton = settingKey
				self.currentSelectionNode = child
			rowNumber+=1
			

		self.makeSelectedButtonColored(self.currentSelectionButton)


	def changeMenuValue(self, clickedNode, labelToChange):
		currentValue = clickedNode.value[0]
		potentialValues = clickedNode.value[1]
		currentValueIndex = potentialValues.index(currentValue)
		nextValue = potentialValues[(currentValueIndex+1)%(len(potentialValues))]
		clickedNode.value = (nextValue, potentialValues)
		labelToChange["text"] = nextValue

		if clickedNode.name == "DIMENSION MODE":
			self.toggle_2d3d()
		elif clickedNode.name == "MODULATION FREQ":
			self.toggleModulationFrequency()
		elif clickedNode.name == "ENABLE PI DELAY":
			self.toggleEnablePiDelay()
		elif clickedNode.name == "CLOCK":
			self.toggleClockSource()
		elif clickedNode.name == "CLOCK FREQ":
			self.toggleClockFreq()
		elif clickedNode.name == "_RESTART BBB_":
			self.restartBBB()
		elif clickedNode.name == "_SHUTDOWN BBB_":
			self.shutdownBBB()
		elif clickedNode.name == "HDR SETTING":
			self.toggleHDRSetting()


	def makeSelectedButtonColored(self, button):
		button['bg'] = '#9ee3ff'

	def makbutton2White(self, button):
		button['bg'] = self.buttonColor

	def setPreviousImage(self,img):
		self.mainArea.previousImage = img
		self.mainArea.winfo_children()[4].create_image(0,0,anchor=NW, image=img)
		self.mainArea.winfo_children()[4].pack()

	def setPreviousImage_2(self, img1, img2):
		self.mainArea.prevImg1 = img1
		self.mainArea.prevImg2 = img2
		self.mainArea.winfo_children()[4].create_image(0,200,anchor=NW, image=img1)
		self.mainArea.winfo_children()[4].create_image(720,200,anchor=NW, image=img2)
		self.mainArea.winfo_children()[4].pack()

	def setDCSImage(self, img):
		self.mainArea.fourDCSImages = img
		self.mainArea.winfo_children()[0].pack_forget()
		self.mainArea.winfo_children()[0].create_image(0,0,anchor=NW, image=img)
		self.mainArea.winfo_children()[0].pack()

	def getDCSImage(self):
		if '_2D_' in self.previousImages[len(self.previousImages)-1]:
			binPath = self.previousImages[len(self.previousImages)-1]
			pngPath = readBinary.convertBINtoPNG(binPath, self.clockFreq)
		else: 
			pngPath = 'noDCS.jpg'
		return Image.open(pngPath)


	def setLiveImage(self, img):
		self.mainArea.liveImg = img
		self.mainArea.winfo_children()[5].pack_forget()
		self.mainArea.winfo_children()[5].create_image(0,0,anchor=NW, image=img)
		self.mainArea.winfo_children()[5].pack()

	def setCapturingVideoImage(self, img):
		self.mainArea.liveImg = img
		self.mainArea.winfo_children()[5].pack_forget()
		self.mainArea.winfo_children()[5].create_image(0,0,anchor=NW, image=img)
		self.mainArea.winfo_children()[5].pack()


	# def openChildMenu(self, node):

	def selectUp(self, currentSelectionNode):
		currentSelectionIndex = self.menu_tree.currentLevel.index(currentSelectionNode)
		newIndex = max(0, currentSelectionIndex - 1)
		newNodeSelection = self.menu_tree.currentLevel[newIndex]
		self.makbutton2White(self.nodeToButtonDict[currentSelectionNode][0])
		self.makeSelectedButtonColored(self.nodeToButtonDict[newNodeSelection][0])
		self.currentSelectionNode = newNodeSelection
		self.currentSelectionButton = self.nodeToButtonDict[newNodeSelection][0]

	def selectDown(self, currentSelectionNode):
		currentSelectionIndex = self.menu_tree.currentLevel.index(currentSelectionNode)
		newIndex = min(len(self.menu_tree.currentLevel)-1, currentSelectionIndex + 1)
		newNodeSelection = self.menu_tree.currentLevel[newIndex]
		self.makbutton2White(self.nodeToButtonDict[currentSelectionNode][0])
		self.makeSelectedButtonColored(self.nodeToButtonDict[newNodeSelection][0])
		self.currentSelectionNode = newNodeSelection
		self.currentSelectionButton = self.nodeToButtonDict[newNodeSelection][0]

	def clearMenuFrame(self):
		for i in self.menuFrame:
			i.grid_forget()

	def MENU_pressed(self):
		print("MENU PRESSED")
		if self.get_mode() == 0:            #capture
			self.change_mode()
			self.set_live_view(False)
			self.viewingPreviousImages = False
		else:
			print("AT ROOT: ", self.menu_tree.isAtTempRoot())
			if self.menu_tree.isAtTempRoot():
				self.change_mode()
			else:
				self.menu_tree.goUpLevel(self.menu_tree.currentLevel)

	def HDR_pressed(self):
		print("HDR pressed")
		self.HDRmode = 1 - self.HDRmode

	def DISP_short_pressed(self):
		print("DISP SHORT")
		if self.get_mode() == 0:
			#capture mode
			if not self.isTakingVideo:  #ready to take photo
				#not taking video
				if self.viewingPreviousImages:
					#get the next previous image
					# self.setPreviousImage(ImageTk.PhotoImage(self.get_previousImage(self.currentPreviousImage).resize((600,450),Image.ANTIALIAS)))
					if len(self.previousImages) > 0:
						# self.setPreviousImage(ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((1440,950),Image.ANTIALIAS)))
						self.setPreviousImage_2(ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((720,425),Image.ANTIALIAS)),ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage-1).resize((720,425),Image.ANTIALIAS)))
						print("DISPLAYING: ", self.previousImages[self.currentPreviousImage])
						self.currentPreviousImage = (self.currentPreviousImage-2)%len(self.previousImages)
						self.update_display()
				else:
					self.change_display()
		else:                           
			self.selectUp(self.currentSelectionNode)

	def DISP_long_pressed(self):
		# self.setPreviousImage(ImageTk.PhotoImage(self.get_previousImage(self.currentPreviousImage).resize((600,450),Image.ANTIALIAS)))

		if not self.get_mode() and not self.get_video_state():
			if not self.viewingPreviousImages: 
				self.currentPreviousImage = len(self.previousImages)-1
				# self.setPreviousImage(ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((720,425),Image.ANTIALIAS)))
				self.setPreviousImage_2(ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage).resize((720,425),Image.ANTIALIAS)),ImageTk.PhotoImage(self.get_previousImage_BIN(self.currentPreviousImage-1).resize((720,425),Image.ANTIALIAS)))
							
				self.currentPreviousImage = (self.currentPreviousImage-1)%len(self.previousImages)
				#capture mode and not taking video
			self.toggle_prev_image()
			self.set_live_view(False)
			self.update_display()

	def EXP_short_pressed(self):
		print("EXPO PRESSED")
		if self.get_mode() == 0:            #capture
			self.change_exposure(self.dimensionMode)
		else:                               #menu mode
			self.selectDown(self.currentSelectionNode)

	def EXP_long_pressed(self):
		if self.get_mode() == 0:            #capture
			print("TOGGLE LIVE VIEW")
			self.toggle_live_view()
			self.viewingPreviousImages = False
			self.set_video_state(False)
			self.setCapturingVideoImage(ImageTk.PhotoImage(Image.open('noLiveViewAvailable.jpg').resize((1440,950),Image.ANTIALIAS)))
			self.update_display()
			self.capture_video(True)
		else:                           
			self.EXP_short_pressed()

	def ACTN_short_pressed(self):
		print("ACTN PRESSED")
		if self.get_mode() == 0:            #capture
			if not self.isTakingVideo:  #ready to take photo
				if self.HDRmode:
					self.HDRWrapper(self.HDRTestSetting)
				else:
					print("PHOTO exp", self.exposure2d)
					self.take_photo(False)
				
				if self.viewingPreviousImages:
					self.setPreviousImage_2(ImageTk.PhotoImage(self.get_previousImage_BIN(len(self.previousImages)-1).resize((720,425),Image.ANTIALIAS)),ImageTk.PhotoImage(self.get_previousImage_BIN(len(self.previousImages)-2).resize((720,425),Image.ANTIALIAS)))
					self.currentPreviousImage = (self.currentPreviousImage-2)%len(self.previousImages)
					self.update_display()
				else:
					self.DISP_long_pressed()
			else:
				print("END VIDEO")          #currently taking video
				self.mainImportantData["VIDEO"] = 'NO'
				self.set_video_state(False)
				self.set_live_view(False)
				self.change_display(4)
				self.setPreviousImage_2(ImageTk.PhotoImage(self.get_previousImage_BIN(len(self.previousImages)-1).resize((720,425),Image.ANTIALIAS)),ImageTk.PhotoImage(self.get_previousImage_BIN(len(self.previousImages)-2).resize((720,425),Image.ANTIALIAS)))
				self.currentPreviousImage = (self.currentPreviousImage-2)%len(self.previousImages)
				self.update_display()
		else:                               #menu mode
			self.changeMenuValue(self.currentSelectionNode, self.nodeToButtonDict[self.currentSelectionNode][1])


	def ACTN_long_pressed(self):
		if not self.get_mode() and not self.get_video_state():  
			#capture mode and ready to take video

			self.set_video_state(True)
			self.set_live_view(True)
			self.viewingPreviousImages = False

			# self.setCapturingVideoImage(ImageTk.PhotoImage(Image.open('video.jpg').resize((1440,950),Image.ANTIALIAS)))
			# self.change_display(5) #to live view/video capture image
			self.mainImportantData['VIDEO'] = 'YES'
			self.update_display()
			self.capture_video(False)
		else:                               
			#else is same as short press
			self.ACTN_short_pressed()

	# def rapidFireUpdate(self):
	# 	r = randint(0,1)
	# 	if self.showingLiveView:
	# 		img = self.get_live_image_temp(r)
	# 		self.setLiveImage(img)
	# 		self.after(50, self.rapidFireUpdate)	
		#absolute  ^ minimum delay is 3ms, below that it drops frames
		#keep high until we need to push it

	def directoryCounter(self, path):

		numFolders = 0
		numFiles = 0
		for _, folderNames, fileNames in os.walk(path):
			numFolders+=len(folderNames)
			numFiles +=len(fileNames)

		return numFolders, numFiles

	def writeImageMetaFile(self, path):
		newFile = open(path, 'w+')
		#time 
		newFile.write(datetime.utcnow().strftime("%m%d%H%M%S.%f"))

		#i2c data
		#self.updateI2Cdata(0, i2c.getTemperature(),0)
		for data in self.I2Cdata:
			newFile.write(str(data) + ":" + str(self.I2Cdata[data])+'\n')

		#cam settings
		for data in self.mainImportantData:
			newFile.write(str(data) + ":" + str(self.mainImportantData[data])+'\n')
		newFile.close()

	def writeVideoMetaFile(self, vid_id, path, start, end, numFrames):
		newFile = open(path+"video_"+str(vid_id)+"_meta.txt", 'w+')
		
		#timeStart, timeEnd, number of frames, camera settings

		newFile.write(vid_id + '\n' + start + '\n' + end + '\n' + str(numFrames) + '\n')
		newFile.close()

	def take_photo(self, write_to_temp, vid_id=0):
		#if vid_id is zero, it means we don't care about associating this picture with a video
		#i.e. a picture is being taken or we are in live view
		print("TAKE PHOTO")

		if write_to_temp:
			elementLocation = "./live_view_temp/"
		else:
			elementLocation = "./images/"

		fileLocation = elementLocation+str(datetime.utcnow().strftime("%m%d%H%M%S.%f"))

		if not self.dimensionMode:		#2d
			returnedFiles = uiFunctionCalls.capturePhotoCommand2D(fileLocation+"_2D_")
			# returnedFile = [] #TEMP
		else:
			returnedFiles = uiFunctionCalls.capturePhotoCommand3D(fileLocation+"_3D_")
			# returnedFile = [] #TEMP
		self.previousImages += returnedFiles
		# returnedFileName = str(returnedFile[0])
		# returnedFileName = "filename"		#TEMPORARY, UNCOMMENT ABOVE LINE

		csvFile = open(self.currentCSVFile, 'a')
		writer = csv.writer(csvFile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		for file in returnedFiles: 
			if not write_to_temp:
				#update CSV
				
				#CSV FORMAT
				#index, imageLocation, metadataLocation
				metaFile = fileLocation+"_meta.txt"
				self.writeImageMetaFile(metaFile)
				writer.writerow([self.numPreviousImages, file, vid_id, metaFile])
				self.numPreviousImages +=1
		
		csvFile.close()
		return fileLocation

	def capture_video(self, write_to_temp = False):
		#if we are taking a video, we write to a permanent location
		#otherwise, we are in live view and want to write to a temporary location and delete later
		print("TAKE VIDEO")
		# numFolders, numFiles = self.directoryCounter("./images")

		timeStart = datetime.utcnow().strftime("%m%d%H%M%S")
		frameCounter =0

		#this looks awkward but we need two while loops because we don't want user to change
		#HDR setting in the middle of a capture... that would be confusing
		if self.HDRmode:
			while self.showingLiveView:
				photoLocation = self.HDRWrapper(self.HDRTestSetting, timeStart)
				img = self.get_live_image(photoLocation)
				self.setLiveImage(img)
				frameCounter +=1
				self.nonRecursiveButtonCheck()
				
		else:
			while self.showingLiveView:
				photoLocation = self.take_photo(write_to_temp, timeStart)
				# img = self.get_live_image(photoLocation)
				# self.setLiveImage(img)
				frameCounter +=1
				self.nonRecursiveButtonCheck()

		timeEnd = datetime.utcnow().strftime("%m%d%H%M%S")

		if frameCounter > 0:
			self.writeVideoMetaFile(timeStart, "./images/", timeStart, timeEnd, frameCounter)


	def change_mode(self):
		self.mode = 1 - self.mode
		self.change_title(MODE_OPTIONS[self.mode])
		self.display = max(-1,-1*(self.display+1))
		self.update_display()

	def change_display(self, val=10):
		#10 is arbitrary display that doesn't exist
		if val == 10:
			self.display = (self.display +1)%4
		else:
			self.display = val
		self.update_display()

	def change_exposure(self, mode):
		if mode:
			#3d
			uiFunctionCalls.change3dExposure(self.exposure3d)
			exposureIndex = EXPOSURE_OPTIONS.index(self.exposure3d)
			self.exposure3d = EXPOSURE_OPTIONS[(exposureIndex+1)%NUM_EXPOSURES]
			self.mainImportantData['EXP 3D'] = self.exposure3d
			print("EXP3D: ", self.exposure3d)
		else:
			#2d
			uiFunctionCalls.change2dExposure(self.exposure2d)
			exposureIndex = EXPOSURE_OPTIONS.index(self.exposure2d)
			self.exposure2d = EXPOSURE_OPTIONS[(exposureIndex+1)%NUM_EXPOSURES]
			self.mainImportantData['EXP 2D'] = self.exposure2d
			print("EXP2D: ", self.exposure2d)
		self.update_display()

	def set_exposure(self,mode, val):
		if mode:
			self.exposure3d = val
			print("IN HERE: ", self.exposure3d)
			uiFunctionCalls.change3dExposure(self.exposure3d)
		else:
			self.exposure2d = val
			print("IN HERE: ", self.exposure2d)
			uiFunctionCalls.change2dExposure(self.exposure2d)


	def change_title(self, newTitle):
		self.title = newTitle 

	def toggle_2d3d(self):
		self.dimensionMode = 1 - self.dimensionMode
		uiFunctionCalls.toggle2d3dMode(self.dimensionMode)

	def set_2d3d(self, x):
		self.dimensionMode = x
		uiFunctionCalls.toggle2d3dMode(self.dimensionMode)

	def toggleModulationFrequency(self):
		self.modFreq = 1 - self.modFreq
		uiFunctionCalls.setModulationFrequency(self.modFreq)

	def setModulationFrequency(self, x):
		self.modFreq = x
		uiFunctionCalls.setModulationFrequency(self.modFreq)

	def toggleEnablePiDelay(self):
		self.piDelay = 1 - self.piDelay
		uiFunctionCalls.enablePiDelay(self.piDelay)

	def setPiDelay(self, x):
		self.piDelay = x
		uiFunctionCalls.enablePiDelay(self.piDelay)

	def toggleClockSource(self):
		self.clockSource = 1 - self.clockSource
		uiFunctionCalls.changeClockSource(self.clockSource)

	def setClock(self, x):
		self.clockSource = x
		uiFunctionCalls.changeClockSource(self.clockSource)

	def toggleClockFreq(self):
		self.clockFreq = (2*self.clockFreq)%42	#rotates between 6,12,24
		mult = self.clockFreq*3
		div = 25*3
		i2c.writeClock(mult, div)

	def setClockFreq(self, x):
		self.clockFreq = x
		mult = self.clockFreq*3
		div = 25*3
		#the 3 is necessary because the mult must be between 15 and 90
		#our clockFreq options (6,12,24) so these values *3 are in this range
		i2c.writeClock(mult, div)

	def toggleHDRSetting(self):
		self.HDRTestSetting = (self.HDRTestSetting + 1) % len(TEMP_MENUTREE['root']['HDR SETTING'][1])


	def toggleEnableCapture(self):
		self.enableCapture = 1 - self.enableCapture
		uiFunctionCalls.enableCapture(self.enableCapture)

	def updateI2Cdata(self, d,t,p):
		self.I2Cdata["direction"] = d
		self.I2Cdata["temperature"] = t 
		self.I2Cdata["pressure"] = p 

	def doHDRtest(self, _2d3dModeOptions, expOptions, piOptions, modFreqOptions, vid_id):
		print("DOING HDR TEST")

		for dimMode in _2d3dModeOptions:			#2d and 3d mode
			self.set_2d3d(dimMode)
			for exp in expOptions:
				self.change_exposure(self.dimensionMode)
				for pi in piOptions:
					self.setPiDelay(pi)
					for freq in modFreqOptions:
						self.setModulationFrequency(freq)
						singleRepresentativePhoto = self.take_photo(False, vid_id)
						#if you're doing an HDR test, you always want to store the image (ie temp write is False)
		#an HDR test takes a LOT of images, but we only return one (doesn't matter which)
		#to display to the user in the live view
		#it might be really trippy to be baraded by images with different exposures
		return singleRepresentativePhoto

	def HDRWrapper(self, setting, vid_id=0):
		_2d3d, exp, pi, modFreq = HDR_SETTINGS[setting]
		return self.doHDRtest(_2d3d, exp,pi, modFreq, vid_id)


	def restartBBB(self):
		print("YO IM RESTARTING THE BBB")
		camera_power.turn_off(gpio.LED(pg.bbb0_ctrl_GPIO()), gpio.Button(pg.bbb0_reset_GPIO()))
		camera_power.turn_off(gpio.LED(pg.bbb0_ctrl_GPIO()), gpio.Button(pg.bbb0_reset_GPIO()))
		# camera_power.connect_both_cameras()
		# camera_power.turn_on_BBBx(0)
		# camera_power.turn_on_BBBx(1)

	def shutdownBBB(self):
		print("AYYO TIME TO SHUTDOWN")
		camera_power.turn_off(gpio.LED(pg.bbb0_ctrl_GPIO()), gpio.Button(pg.bbb0_reset_GPIO()))
		camera_power.turn_off(gpio.LED(pg.bbb0_ctrl_GPIO()), gpio.Button(pg.bbb0_reset_GPIO()))
		# camera_power.connect_both_cameras()
		# camera_power.turn_on_BBBx(0)
		# camera_power.turn_on_BBBx(1)






def main():
	camera_power.connect_both_cameras()

	# camera_power.turn_on_BBBx(0)
	# camera_power.turn_on_BBBx(1)
	root = tk.Tk()
	root.overrideredirect(False)		
	root.attributes('-fullscreen', True)
	app = Application(master=root)
	app.buttonCheck()
	app.mainloop()	# turns out this is actually really important and GUI won't run otherwise

if __name__ == '__main__':
	main()