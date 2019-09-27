# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Fri Aug 16 19:52:17 2019

@author: jake
"""

import os
import csv
from datetime import datetime
import numpy as np
#import matplotlib.pyplot as plt
import threading
import time
import promapi as papi
import multiprocessing as mp

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
            cams=[0, 1],
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
        self.filequeue = mp.Queue()   
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
                self.writecommand(cmd)
                cmd = log.readline().strip('\n')
        os.system('taskset -cp 0 {0:d}'.format(os.getpid()))
        mp.Process(target= startsaving, args = (self.filequeue, )).start()

    def shutdown(self):
        self.metafile.close()
        self.filequeue.put('EOF')
    
    def writecommand(self,commandstring, savefile = None):
        if self.debugMode:
            print(commandstring)
        elif savefile is None:
            for camnum in self.cams:
                response = papi.apiCall(commandstring, camnum)
            print('{}: {}'.format(commandstring,int.from_bytes(response,'little')))
            return response
        else:
            for camnum in self.cams:
                data = papi.apiCall(commandstring, camnum)
                self.enqueue(savefile, data)
            
    def enqueue(self, savefile, data):
        self.filequeue.put(savefile)
        self.filequeue.put(data)

        
    def enabledll(self):
        self.writecommand('w ae 4')
        
    def disabledll(self):
        self.writecommand('w ae 1')
        
    def captureImage(self,capSet,framenum=None, filename=None):        
        #This is a bit of funky logic to allow captureHDRImage to make calls to capture Image
        with self.imagelock:            
            self.numimages = self.numimages + 1
            if (framenum is None):                
                self.numframes = self.numframes + 1
                framenum = self.numframes
            if (filename is None):
                self.frametag = 'single'
                filename = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
            #
            cmdlist = capSet.listCmds(self.currSet)
            imgCmd = capSet.imgCmd()        
            self.updateCapSet(capSet)
            #
            if capSet.measureTemp:
                currTemp = self.getTemp()
            else:
                currTemp = None
            #
            for cmd in cmdlist:                
                self.writecommand(cmd)
    
            #self.writecommand(imgCmd,'> {}.bin'.format(os.path.join(self.outputpath,filename)))
            #self.writecommand(imgCmd,'> {}.bin'.format(newfilename))
            #newfilename = os.path.join(self.outputpath,filename)
            self.writecommand(imgCmd, filename)
            self.filenames.append(filename)
            #
            capAtts = vars(capSet)
            #self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], 'cams', str(self.cams)] + list(itertools.chain(*capAtts.items())))
            self.metawriter.writerow([filename, datetime.now().strftime('%H%M%S.%f)')[:-3], str(self.cams), self.numimages, framenum, str(self.currvideo), self.frametag] + list(capAtts.values()) + [currTemp])
            
    
    def captureHDRImage(self,capSets):
        self.movielock.acquire()
        self.numframes = self.numframes + 1
        self.frametag = 'HDR'
        self.HDRtimer(capSets, 1, 0, 1)

        
    def captureCalImage(self, numframes=10, exposureTime=3000, calTemp=42):
        self.enabledll()
        cS = self.calCapSet(exposureTime)
        self.preHeat(calTemp)
        self.captureHDRVideo(cS, numframes)
        with self.movielock:
            self.disabledll()
            print('Finished Calibration Capture')
            
    def HDRtimer(self,capSets, nImag, i, j):
        filename = 'image{0}_{1:03d}-{2:02d}'.format(self.timestamp,self.numframes+j, i)
        if i < len(capSets) - 1:
            threading.Timer(1/self.framerate, self.HDRtimer,args=[capSets, nImag, i+1, j]).start()
        elif (i == len(capSets) - 1) and j < nImag:
            threading.Timer(1/self.framerate, self.HDRtimer,args=[capSets, nImag, 0, j+1]).start()
        self.captureImage(capSets[i], self.numframes + j, filename)
        if (i == len(capSets) - 1) and j == nImag:
            self.currvideo = -1
            self.numframes = self.numframes + nImag
            self.movielock.release()
            print('Finished HDR Capture')
            
    def updateCapSet(self,newcapSet):
        capAtts = vars(newcapSet)
        for attkey in capAtts.keys():
            if not(capAtts[attkey] is None):
                setattr(self.currSet,attkey,capAtts[attkey])
                
    def captureVideo(self,capSet,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        self.videoTimer(capSet, nImag)
        
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
        self.HDRtimer(capSets,nImag, 0, 1)
        
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
        
def startsaving(q):
    os.system('taskset -cp 1 {0:d}'.format(os.getpid()))
    os.system('sudo renice -n -10 -p {0:d}'.format(os.getpid()))
    keepgoing = True
    while keepgoing:    
        filename = q.get()
        print('got filename {}'.format(filename))
        if filename is 'EOF':
            keepgoing = False
            print('Caught EOF, shutting down')
        else:            
            data = q.get()
            print('writing data, save queue = {}'.format(q.qsize()))
            f = open('/home/pi/images/' + filename + '.bin','wb')
            f.write(data)
            f.close
            print('wrote data')