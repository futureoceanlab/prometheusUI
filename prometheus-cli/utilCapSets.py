from promCliUtil import *
capvals = {'mode': 1, 'piDelay': 1, 'exposureTime': 100, 'modFreq': 1}
cap1 = captureSetting(**capvals)
capvals['exposureTime'] = 300
cap2 = captureSetting(**capvals)
capvals['exposureTime'] = 1000
cap3 = captureSetting(**capvals)
capvals['exposureTime'] = 3000
cap4 = captureSetting(**capvals)
capvals['mode'] = 0
capvals['exposureTime'] = 100
cap5 = captureSetting(**capvals)
capvals['exposureTime'] = 1000
cap6 = captureSetting(**capvals)
capSet = [cap1, cap2, cap3, cap4, cap5, cap6]
