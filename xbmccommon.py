#
# Common code for xbmc related stuff
#

import xbmc, xbmcaddon
import pickle
import os
import errno
import huecontrol

ADDON_ID = 'service.huecontrol'


__addon__ = xbmcaddon.Addon(id=ADDON_ID)
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonicon__ = os.path.join(__addonpath__, 'icon.png')
__language__ = __addon__.getLocalizedString
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")  # Translate path to change special:// protocol to a normal path


# Just a wrapper to keep icons and title easier consistent
def notify(text, duration=3000, title=None):
    if title == None:
        title = __language__(30000)
    
    xbmc.executebuiltin('Notification("{1}","{2}", {3}, {0})'.format(__addonicon__, title, text, duration))


    
# --- Settings related stuff ---
    
# Make sure profile path exists (it seems to be created when first time the settings are saved from the settings dialog)
try:
    os.makedirs(__profile__)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise


    
class HueControlSettings:
    '''Settings dict stored in a file in the addon userdata folder'''
    
    def __init__(self):
        self.datafile = os.path.join(__profile__, 'bridgesettings.pck')
        self.data = {}

        if not os.path.isfile(self.datafile):
            self._createdefaultpresets()
        else:
            with open(self.datafile, 'rb') as handle:
                self.data = pickle.loads(handle.read())
                
            if not 'settingsversion' in self.data:
                self._createdefaultpresets()
                self.data['settingsversion'] = 1
                

    def store(self):
        with open(self.datafile, 'wb') as handle:
            pickle.dump(self.data, handle)
            return True
        
        return False
    
    def _createdefaultpresets(self):
        self.data['scenePlaying'] = {'lights': {}}
        self.data['scenePaused'] = {'lights': {}}
        self.data['scenePreset1'] = {'lights': {}}
        self.data['scenePreset2'] = {'lights': {}}
        self.data['scenePreset3'] = {'lights': {}}
        self.data['scenePreset4'] = {'lights': {}}
        self.data['scenePreset5'] = {'lights': {}}

        for i in range(huecontrol.MAX_LAMPS):
            self.data['scenePlaying']['lights'][str(i+1)] =  {'state':{'on':False}}
            self.data['scenePaused']['lights'][str(i+1)] = {'state':{'on':True, 'bri':100}}
            self.data['scenePreset1']['lights'][str(i+1)] = {'state':{'on':True, 'bri':50, 'colormode':'ct', 'ct':500}}
            self.data['scenePreset2']['lights'][str(i+1)] = {'state':{'on':True, 'bri':100, 'colormode':'ct', 'ct':420}}
            self.data['scenePreset3']['lights'][str(i+1)] = {'state':{'on':True, 'bri':150, 'colormode':'ct', 'ct':340}}
            self.data['scenePreset4']['lights'][str(i+1)] = {'state':{'on':True, 'bri':200, 'colormode':'ct', 'ct':260}}
            self.data['scenePreset5']['lights'][str(i+1)] = {'state':{'on':True, 'bri':250, 'colormode':'ct', 'ct':180}}
            
        self.store()
            
            
            