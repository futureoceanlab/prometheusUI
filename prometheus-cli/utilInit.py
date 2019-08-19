# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 17:10:44 2019

@author: jake
"""

from promCliUtil import *
pS = promSession()
capvals = {'mode': 1, 'piDelay': 1, 'exposureTime': 1000, 'modFreq': 1}
cap1 = captureSetting(**capvals)