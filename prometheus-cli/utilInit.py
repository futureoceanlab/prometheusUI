# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 17:10:44 2019

@author: jake
"""

from promCliUtil import *
pS = promSession()
capvals = {'mode': 1, 'piDelay': 1, 'exposureTime': 100, 'modFreq': 1}
cap1 = captureSetting(**capvals)
capvals['exposureTime'] = 300
cap2 = captureSetting(**capvals)
capvals['exposureTime'] = 1000
cap3 = captureSetting(**capvals)
capvals['exposureTime'] = 3000
cap4 = captureSetting(**capvals)
capSet = [cap1, cap2, cap3, cap4]