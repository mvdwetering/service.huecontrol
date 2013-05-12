#
# XBMC Service plugin that controls the brightnes/on state of lamps
#

import json
import httplib
import xbmc,xbmcgui, xbmcaddon
import subprocess,os
import sys
from urlparse import urlparse, parse_qs

import hue
import huecontrol
import time

  
class HuePlayer(xbmc.Player):

    def __init__ (self):
        xbmc.Player.__init__(self)
        
        self.savedlampstate = '{"lights":{}}'
        self.CONTROLLING_LAMPS = 0
        self.addonId = huecontrol.ADDON_ID

        print "--> Init"

    def _setScene(self, scenename):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        self._setState(hueAddon.getSetting(scenename), hueAddon.getSetting("brightnessonly" + scenename) == "true")

    def _setState(self, state, briOnly=False):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        hueAddonDataPath = xbmc.translatePath( hueAddon.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
        hueAddonDataFile = os.path.join(hueAddonDataPath, 'bridgesettings.pck')

        hueAddonSettings = {}

        if (os.path.isfile(hueAddonDataFile)):
            with open(hueAddonDataFile, 'rb') as handle:
              hueAddonSettings = pickle.loads(handle.read())

    
        lamps = []
        for i in range(huecontrol.MAX_LAMPS):
            strId = str(i)

            if hueAddon.getSetting("lamp" + strId) == "true":
                lamps.append(i)
            
        bridge = hue.Bridge(ip=hueAddonSettings["bridgeip"], id=hueAddonSettings["bridgeid"], username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
        bridge.setFullStateLights(state, lamps, briOnly)

    def onPlayBackStarted(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)

        print "--> onPlayBackStarted"
        print xbmc.Player().getTotalTime()
        print hueAddon.getSetting("minvideolength")

        if xbmc.Player().isPlayingVideo() and (xbmc.Player().getTotalTime() >= (float(hueAddon.getSetting("minvideolength")) * 60) or xbmc.Player().getTotalTime() == 0):
            if (self.CONTROLLING_LAMPS == 0):
                hueAddonDataPath = xbmc.translatePath( hueAddon.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
                hueAddonDataFile = os.path.join(hueAddonDataPath, 'bridgesettings.pck')

                hueAddonSettings = []

                if (os.path.isfile(hueAddonDataFile)):
                    with open(hueAddonDataFile, 'rb') as handle:
                      hueAddonSettings = pickle.loads(handle.read())

                bridge = hue.Bridge(ip=hueAddonSettings["bridgeip"], id=hueAddonSettings["bridgeid"], username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
                self.savedlampstate = bridge.getFullState()

            self.CONTROLLING_LAMPS = 1
            self._setScene("scenePlaying")
            
    
    def onPlayBackEnded(self):
        print "--> onPlayBackEnded"
        print xbmc.Player().getTotalTime()
            
        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)
            
        self.CONTROLLING_LAMPS = 0

    def onPlayBackStopped(self):
        print "--> onPlayBackStopped"

        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)

        self.CONTROLLING_LAMPS = 0
        
        
    def onPlayBackPaused(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackPaused"
        print xbmc.Player().getTotalTime()

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePaused")


    def onPlayBackResumed(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackResumed"
        print xbmc.Player().getTotalTime()

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePlaying")




# Service mode
huePlayer = HuePlayer()

while(not xbmc.abortRequested):
    # Getting new reference to the addon, this will also make sure the settings are reloaded so changes
    # throught the settings UI are used. Otherwise the service will keep having the settings from when the service was started
    # TODO: see if this can be made better, this is just silly
    ##hueAddon = xbmcaddon.Addon(id='service.huecontrol')
    #print "Loopy"
    xbmc.sleep(1000)

 

    