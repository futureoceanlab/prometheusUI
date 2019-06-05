#!/usr/bin/env python3

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
from datetime import datetime

BUTTON_LONGPRESS_TIME = 1
EXPOSURE_OPTIONS = [30, 100, 300, 1000, 3000]
NUM_EXPOSURES = len(EXPOSURE_OPTIONS)
MODE_OPTIONS = ["CAPTURE", "MENU"]
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
											} ,
							'Key1': 'val1'

							}
						}

TEMP_MENUTREE ={'root': {
						"DIMENSION MODE": ('2D', ['2D','3D']),
						"MODULATION FREQ": (0, [0,1]),
						"ENABLE PI DELAY": (0, [0,1]),

}
	
}


class MenuTree():
	# A tree is a list of nodes 
	# Nodes have a name and a list of child nodes
	# The purpose of the tree is to make it easy to get
	# the previous and next level of the menu

	def __init__(self, treeStructure):
		self.root = 'root'
		self.numberOfLevels = 0
		self.tree = self.makeTree(treeStructure)
		self.currentLevel = self.tree

	def makeTree(self, treeStructure):
		if type(treeStructure) is not dict:
			return treeStructure
		treeFromHere = []
		for key in treeStructure:
			treeFromHere.append(TreeNode(key, self.makeTree(treeStructure[key])) )
			
		return treeFromHere

	def getSelectionLevel(self, selection):
		return selection.getImmediateChildren()

	def traverseDownToSelectionLevel(self, selection):
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
			self.children = childrenOrValue
			self.value = None
		else:
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

		self.exposure2d = 30
		self.exposure3d = 30
		self.title = "CAPTURE"
		self.modFreq = 0 
		self.piDelay = 0 
		self.enableCapture = 0 

		#states
		self.isTakingVideo = False
		self.showingLiveView = False
		self.mode = 0       #   0 is capture; 1 is menu
		self.display = 0    
		# DISPLAY INDEXES
		# There are 4 main displays in capture mode (0,1,2,3)
		# The 'show previous image' display is 7 because (7+1)%4=0 
		# 	so it goes back to display 0 (see change_display())
		# The 'menu display' is -1 because it is the last display in the
		# menu list self.mainArea.winfo_children and (-1+1)%4 = 0 
		# 0  --  4x DCS images  
		# 1  --  point cloud
		# 2  --  'rich data' - state of the system
		# 3  --  color map image
		# 7  --  previous image 
		# -1 --  menu display

		#previous image settings
		self.viewingPreviousImages = False
		self.currentPreviousImage = 0
		self.dimensionMode = 0

		#frame areas of the UI
		self.topArea = None
		self.mainArea = None
		self.dataArea = None
		self.menuFrame = None

		#data contained in the UI 
		self.mainImportantData = {'Battery': '50%', 'Mem': str(43.2)+'GB', 'S/N ratio': 0.6, 'EXP 2D':self.exposure2d, 'EXP 3D': self.exposure3d} 
		self.richData = {'EXP 2D':self.exposure2d, 'EXP 3D': self.exposure3d}
		self.menu_tree = MenuTree(MENUTREE)
		self.temp_menu_tree = MenuTree(TEMP_MENUTREE)
		self.previousImage = 'ocean.jpg'
		self.previousImages = ['ocean.jpg','reef.jpg']
		self.currentSelectionButton = None
		self.currentSelectionNode = None
		self.nodeToButtonDict = {}

		#button information
		self.MENU_BTN = gpio.Button(21, pull_up=True)
		self.DISP_BTN = gpio.Button(20, pull_up=True)
		self.EXPO_BTN = gpio.Button(16, pull_up=True)
		self.ACTN_BTN = gpio.Button(12, pull_up=True)
		self.MENU_BTN.when_pressed = self.MENU_pressed
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
		self._geom = '200x200+0+0'
		master.geometry("{0}x{1}+0+0".format(master.winfo_screenwidth(), master.winfo_screenheight()))
		master.bind('<Escape>',self.toggle_geom)
		self.create_layout()

	

	def buttonCheck(self):
		# The function that continuously checks the state of the buttons

		#MENU BUTTON is just short press so it is handled in __init__

		# DISPLAY BUTTON
		if (time.time() - self.dispSinceLongheld)>1:
			if self.DISP_BTN.is_pressed and not self.dispBtnState:
				#button is being pressed down 
				self.dispBtnState = 1
				self.dispHeldStart = time.time()

			if not self.DISP_BTN.is_pressed and self.dispBtnState:
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
					self.DISP_long_pressed()
					self.dispBtnState = 0
					self.dispSinceLongheld = time.time()


		# EXPOSURE BUTTON
		if (time.time() - self.expoSinceLongheld)>1:
			if self.EXPO_BTN.is_pressed and not self.expoBtnState:
				#button is being pressed down 
				self.expoBtnState = 1
				self.expoHeldStart = time.time()

			if not self.EXPO_BTN.is_pressed and self.expoBtnState:
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
					self.EXP_long_pressed()
					self.expoBtnState = 0
					self.expoSinceLongheld = time.time()


		#ACTION BUTTON
		if (time.time() - self.actnSinceLongheld)>1:
			if self.ACTN_BTN.is_pressed and not self.actnBtnState:
				#button is being pressed down 
				self.actnBtnState = 1
				self.actnHeldStart = time.time()

			if not self.ACTN_BTN.is_pressed and self.actnBtnState:
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
					self.ACTN_long_pressed()
					self.actnBtnState = 0
					self.actnSinceLongheld = time.time()

		# This allows for the button checker to run continously, 
		# alongside the mainloop
		self.master.after(50, self.buttonCheck)

	def checkBeagle(self):
		camera_power.connect_both_cameras()
		#camera_power.turn_on_BBBx(0)
		#camera_power.turn_on_BBBx(1)
		self.master.after(10000, self.buttonCheck)

	def get_mode(self):
		return self.mode

	def get_display(self):
		return self.display

	def get_exposure2d(self):
		return self.exposure2d

	def get_exposure3d(self):
		return self.exposure3d

	def get_title(self):
		return MODE_OPTIONS[self.mode]

	def get_mainImportantData(self):
		return self.mainImportantData

	def get_video_state(self):
		return self.isTakingVideo

	def get_live_view_state():
		return self.showingLiveView()

	def get_previousImage(self, x):
		return ImageTk.PhotoImage(Image.open(self.previousImages[x]).resize((600,450),Image.ANTIALIAS))

	def get_four_DCS_images(self):
		return [ImageTk.PhotoImage(Image.open(self.previousImage).resize((300,225),Image.ANTIALIAS)),
				ImageTk.PhotoImage(Image.open(self.previousImage).resize((300,225),Image.ANTIALIAS)),
				ImageTk.PhotoImage(Image.open(self.previousImage).resize((300,225),Image.ANTIALIAS)),
				ImageTk.PhotoImage(Image.open(self.previousImage).resize((300,225),Image.ANTIALIAS))]

	def get_PC_image(self):
		return ImageTk.PhotoImage(Image.open(self.previousImage).resize((600,450),Image.ANTIALIAS))

	def get_colorMap_image(self):
		return ImageTk.PhotoImage(Image.open(self.previousImage).resize((800,480),Image.ANTIALIAS))
		
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

	def toggle_prev_image(self):
		if self.display == 7:
			self.display = 0
			self.viewingPreviousImages = False
		else:
			self.display = 7
			self.viewingPreviousImages = True

	def toggle_video_state(self):
		self.isTakingVideo = not self.isTakingVideo

	def update_display(self):
		# function that is called after every button push to update
		# the state of the display

		#update title
		self.topArea["text"] = self.get_title()

		#update data
		self.dataArea['text'] = self.get_mainImportantData_string()

		#update main area dimensions
		#the display below is the display that the screen is CHANGING TO
		#not the one that it is coming from
		display = self.get_display()

		#erase everything that goes in main area
		self.menuFrame.grid_forget()
		for i in [0,1,2,3,4]:
			self.mainArea.winfo_children()[i].pack_forget()

		if display == -1 or display == 7 or display == 2:
			#erase the data grid
			self.winfo_children()[2].grid_forget()

		#now display things we want
		if display == -1:
			self.mainArea.winfo_children()[5].grid()
		else:
			self.mainArea.winfo_children()[min(4, display)].pack()

		if display == 0:
			self.winfo_children()[2].grid(row=1, column=5,sticky=W+N+E+S)


	def create_layout(self):

		#setting up all of the displays and hiding the ones that are not
		#used at the inital turn on

		self.pack(fill=BOTH, expand=True)
		self.columnconfigure(0,weight=3)
		self.columnconfigure(1,weight=1)
		self.rowconfigure(0,weight=1)
		self.rowconfigure(1,weight=5)

		#the 3 main frames

		topLabel = Label(self, text=self.title, relief=RIDGE, borderwidth=5, font=('Helvetica', 16))
		topLabel.grid(row=0, column=0, sticky=W+N+E+S, columnspan=2)

		mainFrame = tk.Frame(self, relief=RIDGE, borderwidth=5)
		mainFrame.grid(row=1,column=0, sticky=W+N+E+S)

		dataLabel = Label(self, text=self.get_mainImportantData_string(), font=('Helvetica', 16), relief=RIDGE, borderwidth=5)
		dataLabel.grid(row=1, column=1, sticky=W+N+E+S)

		self.topArea = topLabel
		self.mainArea = mainFrame
		self.dataArea = dataLabel

		#DCS grid -- display = 0
		DCSgrid = tk.Canvas(mainFrame, width=600, height=450)
		DCSgrid.pack()
		imgs = self.get_four_DCS_images()

		mainFrame.a = a = imgs[0]
		mainFrame.b = b = imgs[1]
		mainFrame.c = c = imgs[2]
		mainFrame.d = d = imgs[3]

		DCSgrid.create_image(0,0, anchor=NW, image=a)
		DCSgrid.create_image(300,0,anchor=NW, image=b)
		DCSgrid.create_image(0,225,anchor=NW, image=c)
		DCSgrid.create_image(300,225,anchor=NW, image=d)


		#Point Cloud -- display = 1
		pointCloudCanvas = tk.Canvas(mainFrame, width=600, height=450)
		img = self.get_PC_image()
		mainFrame.img = img
		pointCloudCanvas.create_image(0,0,anchor=NW, image=img)
		pointCloudCanvas.pack_forget()

		#Rich Data -- display = 2
		richDataGrid = tk.Frame(mainFrame)
		rowNum = 0 
		for key in self.richData:
			dataRowKey = Label(richDataGrid, text=key)
			dataRowKey.grid(row=rowNum,column=0)
			dataRowVal = Label(richDataGrid, text=str(self.richData[key]))
			dataRowVal.grid(row=rowNum,column=1)
			rowNum+=1
		richDataGrid.grid_forget()

		# #Color Map -- display = 3
		colorMapCanvas = tk.Canvas(mainFrame, width=800, height=480)
		imgColor = self.get_colorMap_image()
		mainFrame.imgColor = imgColor
		colorMapCanvas.create_image(0,0,anchor=NW, image=imgColor)
		colorMapCanvas.pack_forget()

		# #PreviousImg -- display = 7
		prevImgCanvas = tk.Canvas(mainFrame, width=800, height=480)
		previousImage = self.get_previousImage(self.currentPreviousImage)
		mainFrame.previousImage = previousImage
		prevImgCanvas.create_image(0,0,anchor=NW, image=previousImage)
		prevImgCanvas.pack_forget()


		self.menuFrame = tk.Frame(mainFrame)
		# self.createMenu(self.menuFrame, self.menu_tree.tree[0], True)
		self.createTempMenu()
		self.menuFrame.grid_forget()

	def createTempMenu(self):

		level = self.menu_tree.getSelectionLevel(self.temp_menu_tree.tree[0])
		self.menu_tree.traverseDownToSelectionLevel(self.temp_menu_tree.tree[0])
		rowNumber = 0
		for child in level: 
			
			settingValue = Label(self.menuFrame, text=child.value[0])
			settingValue.grid(row=rowNumber, column=1)
			settingKey = Button(self.menuFrame, text=str('Change ')+child.name, command=lambda: self.changeMenuValue(child, settingValue))
			self.buttonColor = settingKey.cget('bg')
			settingKey.grid(row=rowNumber, column=0)
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
			self.setModulationFrequency()
		elif clickedNode.name == "ENABLE PI DELAY":
			self.toggleEnablePiDelay()

	def makeSelectedButtonColored(self, button):
		button['bg'] = '#9ee3ff'

	def makeButtonWhite(self, button):
		button['bg'] = self.buttonColor


	def setPreviousImage(self,img):
		self.mainArea.previousImage = img
		self.mainArea.winfo_children()[4].create_image(0,0,anchor=NW, image=img)
		self.mainArea.winfo_children()[4].pack()

	def createMenu(self, previousMenu, clickedNode, atRoot):

		if not atRoot:
			previousMenu.grid_forget()
		newMenu = tk.Frame(self.menuFrame, bg='red', width=750, height=400)
		level = self.menu_tree.getSelectionLevel(clickedNode)
		self.menu_tree.traverseDownToSelectionLevel(clickedNode)
		rowNumber = 0 
		for child in level:
			if child.isLeaf():
				settingKey = Button(self.menuFrame, text=str('Change ')+child.name)
				settingKey.grid(row=rowNumber, column=0)
				settingValue = Label(self.menuFrame, text=child.value)
				settingValue.grid(row=rowNumber, column=1)
			else:
				setting = Button(self.menuFrame, text=child.name, command=lambda : self.createMenu(newMenu,child,False))
				setting.grid(row=rowNumber, column=0)
			rowNumber +=1

	# def openChildMenu(self, node):

	def selectUp(self, currentSelectionNode):
		currentSelectionIndex = self.menu_tree.currentLevel.index(currentSelectionNode)
		newIndex = max(0, currentSelectionIndex - 1)
		newNodeSelection = self.menu_tree.currentLevel[newIndex]
		self.makeSelectedButtonColored(self.nodeToButtonDict[newNodeSelection][0])
		self.makeButtonWhite(self.nodeToButtonDict[currentSelectionNode][0])
		self.currentSelectionNode = newNodeSelection
		self.currentSelectionButton = self.nodeToButtonDict[newNodeSelection][0]

	def selectDown(self, currentSelectionNode):
		currentSelectionIndex = self.menu_tree.currentLevel.index(currentSelectionNode)
		newIndex = min(len(self.menu_tree.currentLevel)-1, currentSelectionIndex + 1)
		newNodeSelection = self.menu_tree.currentLevel[newIndex]
		self.makeSelectedButtonColored(self.nodeToButtonDict[newNodeSelection][0])
		self.makeButtonWhite(self.nodeToButtonDict[currentSelectionNode][0])
		self.currentSelectionNode = newNodeSelection
		self.currentSelectionButton = self.nodeToButtonDict[newNodeSelection][0]

	def clearMenuFrame(self):
		for i in self.menuFrame:
			i.grid_forget()

	def MENU_pressed(self):
		if self.get_mode() == 0:            #capture
			self.change_mode()
		else:
			print("AT ROOT: ", self.menu_tree.isAtTempRoot())
			if self.menu_tree.isAtTempRoot():
				self.change_mode()
			else:
				self.menu_tree.goUpLevel(self.menu_tree.currentLevel)

	def DISP_short_pressed(self):
		if self.get_mode() == 0:
			#capture mode
			if not self.get_video_state():  #ready to take photo
				#not taking video
				if self.viewingPreviousImages:
					#get the next previous image
					self.setPreviousImage(self.get_previousImage(self.currentPreviousImage))
					self.currentPreviousImage = (1 + self.currentPreviousImage)%len(self.previousImages)
					self.update_display()
				else:
					self.change_display()
			else:
				print("TAKING VIDEO --> DOING NOTHING")
		else:                           
			self.selectUp(self.currentSelectionNode)

	def DISP_long_pressed(self):
		self.currentPreviousImage = 0
		self.setPreviousImage(self.get_previousImage(self.currentPreviousImage))
		if self.get_mode() == 0 and not self.get_video_state():  
			#capture mode and not taking video
			self.toggle_prev_image()
			self.update_display()

	def EXP_short_pressed(self):
		if self.get_mode() == 0:            #capture
			if not self.dimensionMode:		#2d
				self.change_exposure2d()
				# uiFunctionCalls.change2dExposure(self.exposure2d)
			else:
				self.change_exposure3d()
				# uiFunctionCalls.change3dExposure(self.exposure3d)
		else:                               #menu mode
			self.selectDown(self.currentSelectionNode)

	def EXP_long_pressed(self):
		if self.get_mode() == 0:            #capture
			print("TOGGLE LIVE VIEW")
			self.toggle_live_view()
		else:                           
			self.EXP_short_pressed()

	def ACTN_short_pressed(self):
		if self.get_mode() == 0:            #capture
			if not self.get_video_state():  #ready to take photo
				fileLocation = "./captureImages/"+str(datetime.utcnow().strftime(
"%m%d%H%M%S"))
				if not self.dimensionMode:		#2d
					# returnedFile = uiFunctionCalls.capturePhotoCommand2D(fileLocation+"_2D_")
					returnedFile = [] #TEMP
				else:
					# returnedFile = uiFunctionCalls.capturePhotoCommand3D(fileLocation+"_3D_")
					returnedFile = [] #TEMP
				self.previousImages = returnedFile + self.previousImages
			else:
				print("END VIDEO")          #currently taking video
				self.toggle_video_state()
		else:                               #menu mode
			self.changeMenuValue(self.currentSelectionNode, self.nodeToButtonDict[self.currentSelectionNode][1])


	def ACTN_long_pressed(self):
		if not self.get_mode() and not self.get_video_state():  
			#capture mode and ready to take video
			self.toggle_video_state()
			self.capture_video()
		else:                               
			#else is same as short press
			self.ACTN_short_pressed()

	def change_mode(self):
		self.mode = 1 - self.mode
		self.change_title(MODE_OPTIONS[self.mode])
		self.display = max(-1,-1*(self.display+1))
		self.update_display()

	def change_display(self):
		self.display = (self.display +1)%4
		print("DISP: ",self.display)
		self.update_display()

	def change_exposure2d(self):
		exposureIndex = EXPOSURE_OPTIONS.index(self.exposure2d)
		self.exposure2d = EXPOSURE_OPTIONS[(exposureIndex+1)%NUM_EXPOSURES]
		self.mainImportantData['EXP 2D'] = self.exposure2d
		self.update_display()
		print("EXP2D: ", self.exposure2d)

	def change_exposure3d(self):
		exposureIndex = EXPOSURE_OPTIONS.index(self.exposure3d)
		self.exposure3d = EXPOSURE_OPTIONS[(exposureIndex+1)%NUM_EXPOSURES]
		self.mainImportantData['EXP 3D'] = self.exposure3d
		self.update_display()
		print("EXP3D: ", self.exposure3d)

	def capture_video(self):
		print("TAKE VIDEO")

	def change_title(self, newTitle):
		self.title = newTitle 

	def toggle_2d3d(self):
		self.dimensionMode = 1 - self.dimensionMode
		# uiFunctionCalls.toggle2d3dMode(self.dimensionMode)

	def setModulationFrequency(self):
		self.modFreq = 1 - self.modFreq
		# uiFunctionCalls.setModulationFrequency(self.modFreq)

	def toggleEnablePiDelay(self):
		self.piDelay = 1 - self.piDelay
		# uiFunctionCalls.enablePiDelay(self.piDelay)

	def toggleEnableCapture(self):
		self.enableCapture = 1 - self.enableCapture
		# uiFunctionCalls.enablePiDelay(self.enableCapture)

	def toggle_geom(self,event):
		geom=self.master.winfo_geometry()
		self.master.overrideredirect(False)
		self.master.geometry(self._geom)
		self._geom=geom



def main():
	# camera_power.connect_both_cameras()
	#camera_power.turn_on_BBBx(0)
	#camera_power.turn_on_BBBx(1)
	root = tk.Tk()
	root.overrideredirect(True)
	# root.geometry((800,480))
	app = Application(master=root)
	app.buttonCheck()
	app.mainloop()

if __name__ == '__main__':
	main()
