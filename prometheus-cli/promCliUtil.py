# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Fri Aug 16 19:52:17 2019

@author: jake
"""

import os
import csv
from datetime import datetime
#import itertools

class captureSetting:
    
    def __init__(
            self,
            mode=None,
            piDelay=None,
            exposureTime=None,
            modFreq=None
            ):
        self.mode = mode
        self.piDelay=piDelay
        self.exposureTime=exposureTime
        self.modFreq=modFreq
        
    def listCmds(self, prevSet=None):
        cmdlist = []
        if (prevSet is None):
            prevSet = captureSetting()
        prevAtts = vars(prevSet)
        currAtts = vars(self)
        if not(currAtts['mode'] == prevAtts['mode']):
            prevAtts['exposureTime'] = None
        for key in currAtts:
            if not(currAtts[key] == prevAtts[key]):
                cmdlist.append(self.attrCmd(key, currAtts[key]))
        #cmdlist.append(self.imgCmd())
        return cmdlist
    
    def attrCmd(self, key, val):
        valDict = {
                "mode": "loadConfig {}",
                "piDelay": "enablePiDelay {}",
                "modFreq": "setModulationFrequency {}"}
        if (key == "exposureTime"):
            if (self.mode == 0):
                return "setIntegrationTime2D {}".format(val)
            else:
                return "setIntregrationTime3D {}".format(val)
        else:
            return valDict[key].format(val)
            
        
    def imgCmd(self):
        if (self.mode == 1):
            return "getDCSSorted"
        else:
            return "getBWSorted"
        

class promSession:
    
    def __init__(
            self,
            startupfilename='startupcommands.txt',
            metadatafilename='capturemetadata.csv',
            outputpath= '../../images',
            buildpath='./build',
            cams=0,
            currSet = None,
            debugMode = False,
            verbose = True
            ):
        if currSet is None:
            self.currSet = captureSetting()
        self.debugMode = debugMode
        self.verbose = verbose
        self.cams = cams
        self.cmdpath = os.path.abspath(os.path.join(buildpath,'prom-cli'))
        self.outputpath = os.path.abspath(os.path.normpath(outputpath))
        #
        self.metafile = open(os.path.join(self.outputpath,metadatafilename),'a',newline='')
        self.metawriter = csv.writer(self.metafile)            
        self.metawriter.writerow(['Filename','Time','Camera','filenum','framenum','vidnum','frametag'] + list(vars(self.currSet).keys()))
        #
        self.timestamp = datetime.now().strftime('%y%m%d%H%M')
        self.startup(startupfilename,cams)
        self.numimages=0
        self.numframes=0
        self.numvideos=0
        self.debugMode = debugMode
        if currSet is None:
            self.currSet = captureSetting()
        self.frametag = 'single'
        self.currvideo = -1

    def startup(self,startupfile,cams):
        with open(startupfile, "r") as log:
    	    cmd = log.readline().strip('\n')
    	    while cmd:
                self.writecommand(cmd,'| hexdump')
                cmd = log.readline().strip('\n')
                
    def shutdown(self):
        self.metafile.close()
    
    def writecommand(self,commandstring,output):
        modcom = "{} -a \"{}\" -i {} {}".format(self.cmdpath, commandstring, self.cams, output)
        if self.verbose:
            print(modcom)
        if not(self.debugMode):
            os.system(modcom)
        
    def captureImage(self,capSet,filename=None):        
        #This is a bit of funky logic to allow captureHDRImage to make calls to capture Image
        self.numimages = self.numimages + 1
        if (filename is None):
            self.numframes = self.numframes+1
            self.frametag = 'single'
            filename = 'image{0}_{1:03d}.bin'.format(self.timestamp,self.numframes)
        #
        cmdlist = capSet.listCmds(self.currSet)
        imgCmd = capSet.imgCmd()        
        self.updateCapSet(capSet)
        #
        for cmd in cmdlist:
            self.writecommand(cmd,'| hexdump')
        self.writecommand(imgCmd,'> {}.bin'.format(os.path.join(self.outputpath,filename)))
        #
        capAtts = vars(self.currSet)
        #self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], 'cams', str(self.cams)] + list(itertools.chain(*capAtts.items())))
        self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], str(self.cams), str(self.numimages), str(self.numframes), str(self.currvideo), self.frametag] + list(capAtts.values()))
        
    
    def captureHDRImage(self,capSets):
        self.numframes = self.numframes + 1
        self.frametag = 'HDR'
        fileprefix = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
        for i in range(len(capSets)):
            filename = fileprefix + '-{0:02d}'.format(i)
            self.captureImage(capSets[i],filename)
            
    def updateCapSet(self,newcapSet):
        capAtts = vars(newcapSet)
        for attkey in capAtts.keys():
            if not(capAtts[attkey] is None):
                setattr(self.currSet,attkey,capAtts[attkey])
                
    def captureVideo(self,capSet,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        for i in range(nImag):
            self.captureImage(capSet)
        self.currvideo = -1
        
    def captureHDRVideo(self,capSets,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        for i in range(nImag):
            self.captureHDRImage(capSets)
        self.currvideo = -1
        

    
