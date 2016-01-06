#
# Common code for Kodi related stuff
#

import xbmc, xbmcaddon
import pickle
import os
import errno
import hue

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


def logDebug(msg):
    xbmc.log(msg, level=xbmc.LOGDEBUG)
    
def logError(msg):
    xbmc.log(msg, level=xbmc.LOGERROR)
    
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
            self._createorupdatedefaultpresets()
        else:
            with open(self.datafile, 'rb') as handle:
                self.data = pickle.loads(handle.read())
                
            if not 'settingsversion' in self.data:
                self._createorupdatedefaultpresets()
                self.data['settingsversion'] = 1
            
            if self.data['settingsversion'] == 1:
                if 'bridgeid' in self.data:
                    oldbridgeid = self.data['bridgeid']
                    self.data['bridgeid'] = "{0}fffe{1}".format(oldbridgeid[0:6], oldbridgeid[6:12]).lower()
                self._createorupdatedefaultpresets()
                self.data['settingsversion'] = 2

    def store(self):
        with open(self.datafile, 'wb') as handle:
            pickle.dump(self.data, handle)
            return True
        
        return False
    
    def _createorupdatedefaultpresets(self):
    
        if not 'scenePlaying' in self.data:
            self.data['scenePlaying'] = {'lights': {}}
        if not 'scenePaused' in self.data:
            self.data['scenePaused'] = {'lights': {}}
        if not 'scenePreset1' in self.data:
            self.data['scenePreset1'] = {'lights': {}}
        if not 'scenePreset2' in self.data:
            self.data['scenePreset2'] = {'lights': {}}
        if not 'scenePreset3' in self.data:
            self.data['scenePreset3'] = {'lights': {}}
        if not 'scenePreset4' in self.data:
            self.data['scenePreset4'] = {'lights': {}}
        if not 'scenePreset5' in self.data:
            self.data['scenePreset5'] = {'lights': {}}

        for i in range(hue.MAX_LAMPS):
            lightId = str(i+1)
            
            if not lightId in self.data['scenePlaying']['lights']:
                self.data['scenePlaying']['lights'][lightId] =  {'state':{'on':False}}
            if not lightId in self.data['scenePaused']['lights']:
                self.data['scenePaused']['lights'][lightId] = {'state':{'on':True, 'bri':100}}
            if not lightId in self.data['scenePreset1']['lights']:
                self.data['scenePreset1']['lights'][lightId] = {'state':{'on':True, 'bri':50, 'colormode':'ct', 'ct':500}}
            if not lightId in self.data['scenePreset2']['lights']:
                self.data['scenePreset2']['lights'][lightId] = {'state':{'on':True, 'bri':100, 'colormode':'ct', 'ct':420}}
            if not lightId in self.data['scenePreset3']['lights']:
                self.data['scenePreset3']['lights'][lightId] = {'state':{'on':True, 'bri':150, 'colormode':'ct', 'ct':340}}
            if not lightId in self.data['scenePreset4']['lights']:
                self.data['scenePreset4']['lights'][lightId] = {'state':{'on':True, 'bri':200, 'colormode':'ct', 'ct':260}}
            if not lightId in self.data['scenePreset5']['lights']:
                self.data['scenePreset5']['lights'][lightId] = {'state':{'on':True, 'bri':250, 'colormode':'ct', 'ct':180}}
            
        self.store()
            
            
            