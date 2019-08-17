# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Fri Aug 16 19:52:17 2019

@author: jake
"""

import os

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
        cmdlist = [];
        if (prevSet is None):
            prevSet = captureSetting()
        prevAtts = vars(prevSet)
        currAtts = vars(self)
        if not(currAtts['mode'] == prevAtts['mode']):
            prevAtts['exposureTime'] = None
        for key in currAtts:
            if not(currAtts[key] == prevAtts[key]):
                cmdlist.append(self.attrCmd(key, currAtts[key]))
        cmdlist.append(self.imgCmd())
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
            startupfile='startupcommands.txt',
            metadatafile='capturemetadata.csv',
            buildpath='./build',
            cams=0,
            currSet = None
            ):
        self.cams = cams;
        self.cmdpath = os.path.abspath(os.path.join(buildpath,'prom-cli'))
        self.startup(startupfile,cams)
        if currSet is None:
            self.currSet = captureSetting()
        
    def startup(self,startupfile,cams):
        with open(startupfile, "r") as log:
    	    cmd = log.readline().strip('\n')
    	    while cmd:
                self.writecommand(cmd,'hexdump')
                cmd = log.readline().strip('\n')
                
    #def shutdown(self):
    
    def writecommand(self,commandstring,output):
        modcom = "{} \"{}\" -i {} | {}".format(self.cmdpath, commandstring, self.cams, output)
        print(modcom)
        #os.system(mod_com)
        
    def captureImage(self,capSet):
        cmdlist = capSet.listCmds(self.currSet)
        self.currSet = capSet
        for cmd in cmdlist:
            self.writecommand(cmd,'hexdump')
    
    def captureHDRImage(self,capSets):
        for capSet in capSets:
            self.captureImage(capSet)
            
    #def captureVideo(self,capSet,nImag):
        
    #def captureHDRVideo(self,capSets,nImag):
        
    #def __openMeta(self):
        
    #def __writeMeta(self):
        
    #def __closeMeta(self):
        

    
