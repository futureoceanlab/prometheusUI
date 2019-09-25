# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Fri Aug 16 19:52:17 2019

@author: jake
"""

import os
import csv
from datetime import datetime
import subprocess
import numpy as np
#import matplotlib.pyplot as plt
import threading
import time
#import itertools

class captureSetting:
    
    def __init__(
            self,
            mode=None,
            piDelay=None,
            exposureTime=None,
            modFreq=None,
            dll=None,
            measureTemp=False
            ):
        self.mode = mode
        self.piDelay=piDelay
        self.exposureTime=exposureTime
        self.modFreq=modFreq
        self.dll=dll
        self.measureTemp = measureTemp
        
    def listCmds(self, prevSet=None):
        cmdlist = []
        if (prevSet is None):
            prevSet = captureSetting()
        prevAtts = vars(prevSet)
        currAtts = vars(self)
        keys = list(currAtts.keys())
        #Treat temperature measurement differently
        keys.remove('measureTemp')
        if not(currAtts['mode'] == prevAtts['mode']):
            prevAtts['exposureTime'] = None
        for key in keys:
            if not(currAtts[key] == prevAtts[key]):
                cmdlist.append(self.attrCmd(key, currAtts[key]))
        #cmdlist.append(self.imgCmd())
        return cmdlist
    
    def attrCmd(self, key, val):
        valDict = {
                "mode": "loadConfig {}",
                "piDelay": "enablePiDelay {}",
                "modFreq": "setModulationFrequency {}",
                "dll": "writeRegister 73 {}"}
        if (key == "exposureTime"):
            if (self.mode == 0):
                return "setIntegrationTime2D {}".format(val)
            else:
                return "setIntegrationTime3D {}".format(val)
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
            cams=2,
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
        self.metawriter.writerow(['Filename','Time','Camera','filenum','framenum','vidnum','frametag'] + list(vars(self.currSet).keys()) + ['Temp'])
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
        self.filenames = list()
        self.framerate = 3
        self.imagelock = threading.Lock()
        self.movielock = threading.Lock()

    def startup(self,startupfile,cams):
        with open(startupfile, "r") as log:
    	    cmd = log.readline().strip('\n')
    	    while cmd:
                self.writecommand(cmd,'| hexdump')
                cmd = log.readline().strip('\n')
                
    def shutdown(self):
        self.metafile.close()
    
    def writecommand(self,commandstring,output=None):
        modcom = "{} -a \"{}\" -i {} {}".format(self.cmdpath, commandstring, self.cams, output)
        #print(modcom)
        if self.verbose:
            print(commandstring)
        if self.debugMode:
            return modcom
        else:
            #os.system(modcom)
            return subprocess.run(modcom, shell=True, stdout=subprocess.PIPE).stdout
        
    def enabledll(self):
        self.writecommand('w ae 4')
        
    def disabledll(self):
        self.writecommand('w ae 1')
        
    def captureImage(self,capSet,filename=None):        
        #This is a bit of funky logic to allow captureHDRImage to make calls to capture Image
        with self.imagelock:
            self.numimages = self.numimages + 1
            if (filename is None):
                self.numframes = self.numframes+1
                self.frametag = 'single'
                filename = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
            #
            cmdlist = capSet.listCmds(self.currSet)
            imgCmd = capSet.imgCmd()        
            self.updateCapSet(capSet)
            #
            if self.currSet.measureTemp:
                currTemp = self.getTemp()
            else:
                currTemp = None
            #
            for cmd in cmdlist:
                #self.writecommand(cmd,'| hexdump')
                returnval = self.writecommand(cmd)
                if not(self.debugMode):
                    self.hexdump(returnval)
    
            #self.writecommand(imgCmd,'> {}.bin'.format(os.path.join(self.outputpath,filename)))
            #self.writecommand(imgCmd,'> {}.bin'.format(newfilename))
            newfilename = os.path.join(self.outputpath,filename) + '.bin'
            self.writecommand(imgCmd,'> {}'.format(newfilename))
            self.filenames.append(newfilename)
            #
            capAtts = vars(self.currSet)
            #self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], 'cams', str(self.cams)] + list(itertools.chain(*capAtts.items())))
            self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], str(self.cams), str(self.numimages), str(self.numframes), str(self.currvideo), self.frametag] + list(capAtts.values()) + [currTemp])
            
    
    def captureHDRImage(self,capSets):
        self.movielock.acquire()
        self.numframes = self.numframes + 1
        self.frametag = 'HDR'
        fileprefix = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
        self.HDRtimer(capSets, fileprefix, 0, 1)
        #for i in range(len(capSets)):
        #    filename = fileprefix + '-{0:02d}'.format(i)
        #    self.captureImage(capSets[i],filename)
        
    def captureCalImage(self, numframes=10, exposureTime=3000, calTemp=42):
        self.enabledll()
        cS = self.calCapSet(exposureTime)
        self.preHeat(calTemp)
        self.captureHDRVideo(cS, numframes)
        with self.movielock:
            self.disabledll()
            print('Finished Calibration Capture')
            
    def HDRtimer(self,capSets,fileprefix,i, j):
        if i < len(capSets) - 1:
            threading.Timer(1/self.framerate, self.HDRtimer,args=[capSets, fileprefix, i+1, j]).start()
        elif (i == len(capSets) - 1) and j > 1:
            self.numframes = self.numframes + 1
            fileprefix = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
            threading.Timer(1/self.framerate, self.HDRtimer,args=[capSets, fileprefix, 0, j-1]).start()
        filename = fileprefix + '-{0:02d}'.format(i)
        self.captureImage(capSets[i],filename)
        if (i == len(capSets) - 1) and j == 1:
            self.currvideo = -1
            self.movielock.release()
            
    def updateCapSet(self,newcapSet):
        capAtts = vars(newcapSet)
        for attkey in capAtts.keys():
            if not(capAtts[attkey] is None):
                setattr(self.currSet,attkey,capAtts[attkey])
                
    def captureVideo(self,capSet,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        self.videoTimer(capSet, nImag)
        #for i in range(nImag):
        #    self.captureImage(capSet)
        #self.currvideo = -1
        
    def videoTimer(self,capSet,i):
        if i > 1:
            threading.Timer(1/self.framerate, self.videoTimer,args=[capSet, i-1]).start()
        self.captureImage(capSet)
        if i == 1:
            self.currvideo = -1
            
        
    def captureHDRVideo(self,capSets,nImag):
        self.movielock.acquire()
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        self.numframes = self.numframes + 1
        self.frametag = 'HDR'
        fileprefix = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
        #for i in range(nImag):
        #    self.captureHDRImage(capSets)
        #self.currvideo = -1
        self.HDRtimer(capSets,fileprefix,0,nImag)
        #print('Finished HDR Video')
        
    def getTemp(self):
        tempCmd = 'getTemperature'
        tempbytes = self.writecommand(tempCmd)
        numtemps = 4
        temps = np.zeros(numtemps)
        for i in range(0,numtemps):
            temps[i] = int.from_bytes(tempbytes[2*i:2*(i+1)],'little')
        return temps.mean()/10
    
    def preHeat(self,target):
        maxcycles = 20
        cycletime = 1
        temps = []
        temps.append(self.getTemp())
        i = 0        
        while temps[-1] < target and i < maxcycles:            
            self.illumDisable()
            self.writecommand('w a4 3')
            time.sleep(cycletime)
            self.writecommand('w a4 0')
            temps.append(self.getTemp())
            i = i+1
        print('Start: {}, End: {}, Cycles: {}'.format(temps[0],temps[-1],i))
        print(temps)
        self.illumEnable()

    def illumDisable(self):
        self.writecommand('w 90 c8')
        print('Illumination Disabled')
        
    def illumEnable(self):
        self.writecommand('w 90 cc')
        print('Illumination Enabled')

    def hexdump(self, chararray):
        outline = ''
        for i in range(0,int(len(chararray)/2)):
            outline = outline + '{:02x}{:02x} '.format(chararray[2*i+1], chararray[2*i])
        print(outline)
        
    def calCapSet(self, exposureTime):
        capvals = {'mode': 1, 'piDelay': 1, 'exposureTime': exposureTime, 'modFreq': 1,'measureTemp':False, 'dll':0}
        capSet = list()
        for i in range(0,50):
            capvals['dll'] = format(i,'x')
            capSet.append(captureSetting(**capvals))
        capvals['mode'] = 0
        capvals['measureTemp'] = True
        capSet.append(captureSetting(**capvals))
        return capSet
    
    
    def meanDCS(self, filename):
        raw = np.fromfile(filename, dtype='uint16')
        DCS = raw.astype('int32') - 2**11
        DCS = np.absolute(DCS)
        DCS = DCS.reshape(320,240,-1).transpose(1,0,2)
        amp = DCS.mean(axis=2)
        print('Mean pixel amplitude is {}'.format(amp.mean().round(2)))
        