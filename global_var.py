SCREEEN_WIDTH = 1080
BUTTON_LONGPRESS_TIME = 1
EXPOSURE_OPTIONS = [30, 100, 300, 1000, 3000]
PI_DELAY_OPTIONS = [0,1]
MOD_FREQ_OPTIONS = [0,1]
NUM_EXPOSURES = len(EXPOSURE_OPTIONS)
MODE_OPTIONS = ["CAPTURE", "MENU"]
CAPTURE_MODE_DISPLAYS = ["DCS IMAGES", "POINT CLOUD", "RICH DATA", "COLOR MAP", "PREVIOUS IMAGES", "LIVE", ""]
PLACEHOLDER_IMG_DIR = "placeholder_img"
CSV_LOG_DIR="csv_log"
HDR_SETTINGS = {0:[[1],[30,100,300,1000,3000],[0],[0]],
			    1:[[1],[300],[0],[0,1]],
			    2:[[0,1],[30,100,300,1000,3000],[0,1],[0,1]]}
			    # setting 0: an exposure test
			    #         1: mod freq test
			    #         2: entire blast
                
MENUTREE = {
    'root':{
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

TEMP_MENUTREE ={
    'root': {
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