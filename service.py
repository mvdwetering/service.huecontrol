#
# XBMC Service plugin that controls the brightnes/on state of lamps
#

import json
import httplib
import xbmc,xbmcgui, xbmcaddon
import subprocess,os
import sys
from urlparse import urlparse, parse_qs
import pickle
import os
import errno

import hue
import huecontrol
import xbmccommon
import time

  
class HuePlayer(xbmc.Player):

    def __init__ (self):
        xbmc.Player.__init__(self)
        
        self.savedlampstate = '{"lights":{}}'
        self.CONTROLLING_LAMPS = 0
        self.addonId = xbmccommon.ADDON_ID

        print "--> Init"

    def _setScene(self, scenename):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        self._setState(__addon__.getSetting(scenename), __addon__.getSetting("brightnessonly" + scenename) == "true")

    def _setState(self, state, briOnly=False):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        __addonpath__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
        __addondatafile__ = os.path.join(__addonpath__, 'bridgesettings.pck')

        hueAddonSettings = {}

        if (os.path.isfile(__addondatafile__)):
            with open(__addondatafile__, 'rb') as handle:
              hueAddonSettings = pickle.loads(handle.read())

    
        lamps = []
        for i in range(huecontrol.MAX_LAMPS):
            strId = str(i+1)

            if __addon__.getSetting("lamp" + strId) == "true":
                lamps.append(i+1)
            
        bridge = hue.Bridge(ip=hueAddonSettings["bridgeip"], id=hueAddonSettings["bridgeid"], username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
        bridge.setFullStateLights(state, lamps, briOnly)

    def onPlayBackStarted(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)

        print "--> onPlayBackStarted"
        print xbmc.Player().getTotalTime()
        print __addon__.getSetting("minvideolength")

        if xbmc.Player().isPlayingVideo() and (xbmc.Player().getTotalTime() >= (float(__addon__.getSetting("minvideolength")) * 60) or xbmc.Player().getTotalTime() == 0):
            if (self.CONTROLLING_LAMPS == 0):
                __addonpath__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
                __addondatafile__ = os.path.join(__addonpath__, 'bridgesettings.pck')

                hueAddonSettings = []

                if (os.path.isfile(__addondatafile__)):
                    with open(__addondatafile__, 'rb') as handle:
                      hueAddonSettings = pickle.loads(handle.read())

                bridge = hue.Bridge(ip=hueAddonSettings["bridgeip"], id=hueAddonSettings["bridgeid"], username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
                self.savedlampstate = bridge.getFullState()

            self.CONTROLLING_LAMPS = 1
            self._setScene("scenePlaying")
            
    
    def onPlayBackEnded(self):
        print "--> onPlayBackEnded"
            
        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)
            
        self.CONTROLLING_LAMPS = 0

    def onPlayBackStopped(self):
        print "--> onPlayBackStopped"

        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)

        self.CONTROLLING_LAMPS = 0
        
        
    def onPlayBackPaused(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackPaused"

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePaused")


    def onPlayBackResumed(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackResumed"

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePlaying")




# Check if the bridge still exists where we expect it
__addon__ = xbmcaddon.Addon(id=xbmccommon.ADDON_ID)
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__language__ = __addon__.getLocalizedString

# Make sure profile path exists (it seems to be created when first time the settings are saved fromthe settings dialog
# I need the directory earlier.
try:
    os.makedirs(__profile__)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
            
__addondatafile__ = os.path.join(__profile__, 'bridgesettings.pck')

hueAddonSettings = {}
hueBridgeOk = False

if (os.path.isfile(__addondatafile__)):
    with open(__addondatafile__, 'rb') as handle:
      hueAddonSettings = pickle.loads(handle.read())

    # Make sure the important settings exist
    if (hueAddonSettings["bridgeip"] and hueAddonSettings["bridgeid"]):
        bridge = hue.BridgeLocator(iprange=xbmc.getIPAddress()).FindBridgeById(hueAddonSettings["bridgeid"], hueAddonSettings["bridgeip"])
        
        if bridge == None:
            xbmccommon.notify(__language__(30019), duration=10000)
        else:
            bridge.username = huecontrol.BRIDGEUSER
            bridge.devicetype = huecontrol.DEVICETYPE
            
            if not bridge.isAuthorized():
                xbmccommon.notify(__language__(30019), duration=10000)
            else:
                hueAddonSettings["bridgeip"] = bridge.ip
                hueAddonSettings["bridgeid"] = bridge.id
                
                # Lets save the stuff back in case it changed
                with open(__addondatafile__, 'wb') as handle:
                    pickle.dump(hueAddonSettings, handle)
                    
                    xbmccommon.notify(__language__(30018))
                

            
            
huePlayer = HuePlayer()

while(not xbmc.abortRequested):
    #print "Loopy"
    xbmc.sleep(1000)

 

    