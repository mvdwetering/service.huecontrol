#
# Common code for Kodi related stuff
#

import xbmc, xbmcaddon
import pickle
import os
import errno
import hue
import huecontrol
import json

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
    
def getConfiguredLampsList():
    lamps = []
    for i in range(1, hue.MAX_LAMPS+1):
        strId = str(i)

        if __addon__.getSetting("lamp" + strId) == "true":
            lamps.append(i)

    return lamps
 
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
        self.datafile = os.path.join(__profile__, huecontrol.SETTINGSFILE) # updated to 2 because of somehow the settings are incompatible and not sure how I can fix it
        self.data = {}

        if not os.path.isfile(self.datafile):
            self._createorupdatedefaultpresets()
        else:
            with open(self.datafile, 'rb') as handle:
                self.data = pickle.load(handle)
                
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
    
    
    def _createorupdatedefaultpreset(self, presetName, state):
        if not presetName in self.data:
            self.data[presetName] = {'lights': {}}
        elif isinstance(self.data[presetName], basestring):
            if self.data[presetName] != "":
                self.data[presetName] = json.loads(self.data[presetName])
            else:
                self.data[presetName] = {}

        for i in range(1, hue.MAX_LAMPS+1):
            lightId = str(i)
            
            if not lightId in self.data[presetName]['lights']:
                self.data[presetName]['lights'][lightId] =  state

 
    def _createorupdatedefaultpresets(self):
        
        self._createorupdatedefaultpreset("scenePlaying", {'state':{'on':False}})
        self._createorupdatedefaultpreset("scenePaused",  {'state':{'on':True, 'bri':100}})
        self._createorupdatedefaultpreset("scenePreset1", {'state':{'on':True, 'bri':50,  'colormode':'xy', "xy":[0.5268,0.4133]}})
        self._createorupdatedefaultpreset("scenePreset2", {'state':{'on':True, 'bri':100, 'colormode':'xy', "xy":[0.4883,0.4149]}})
        self._createorupdatedefaultpreset("scenePreset3", {'state':{'on':True, 'bri':150, 'colormode':'xy', "xy":[0.4412,0.4055]}})
        self._createorupdatedefaultpreset("scenePreset4", {'state':{'on':True, 'bri':200, 'colormode':'xy', "xy":[0.3876,0.3811]}})
        self._createorupdatedefaultpreset("scenePreset5", {'state':{'on':True, 'bri':250, 'colormode':'xy', "xy":[0.3312,0.3400]}})

        self.store()
            
            
            