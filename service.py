#
# Kodi Service plugin that controls the brightness/on state of lamps
#

import json
import httplib
import xbmc,xbmcgui, xbmcaddon
import subprocess,os
import sys
from urlparse import urlparse, parse_qs

import hue
import huecontrol
import xbmccommon
import time

logDebug = xbmccommon.logDebug
logError = xbmccommon.logError
  
class HuePlayer(xbmc.Player):

    def __init__ (self):
        xbmc.Player.__init__(self)
        
        self.savedlampstate = ''
        self.CONTROLLING_LAMPS = 0
        self.addonId = xbmccommon.ADDON_ID

        logDebug("--> Init")

    def _setScene(self, scenename):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        hueAddonSettings = xbmccommon.HueControlSettings()
        
        self._setState(hueAddonSettings.data[scenename], __addon__.getSetting("brightnessonly" + scenename) == "true")

    def _setState(self, state, briOnly=False):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        __addonpath__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
        __addondatafile__ = os.path.join(__addonpath__, 'bridgesettings.pck')

        hueAddonSettings = xbmccommon.HueControlSettings()
    
        lamps = []
        for i in range(hue.MAX_LAMPS):
            strId = str(i+1)

            if __addon__.getSetting("lamp" + strId) == "true":
                lamps.append(i+1)
            
        bridge = hue.Bridge(ip=hueAddonSettings.data["bridgeip"], id=hueAddonSettings.data["bridgeid"], username=hueAddonSettings.data.get("bridgeusername", None))
        bridge.setFullStateLights(state, lamps, briOnly)

    def onPlayBackStarted(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)

        logDebug("--> onPlayBackStarted {0}, {1}".format(xbmc.Player().getTotalTime(), __addon__.getSetting("minvideolength")))

        if xbmc.Player().isPlayingVideo() and (xbmc.Player().getTotalTime() >= (float(__addon__.getSetting("minvideolength")) * 60) or xbmc.Player().getTotalTime() == 0):
            if (self.CONTROLLING_LAMPS == 0):
                __addonpath__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")  # Translate path to change special:// protocol to a normal path
                __addondatafile__ = os.path.join(__addonpath__, 'bridgesettings.pck')

                hueAddonSettings = xbmccommon.HueControlSettings()

                bridge = hue.Bridge(ip=hueAddonSettings.data["bridgeip"], id=hueAddonSettings.data["bridgeid"], username=hueAddonSettings.data.get("bridgeusername", None))
                self.savedlampstate = bridge.getFullState()

            self.CONTROLLING_LAMPS = 1
            self._setScene("scenePlaying")
            
    
    def onPlayBackEnded(self):
        logDebug("--> onPlayBackEnded")
            
        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)
            
        self.CONTROLLING_LAMPS = 0

    def onPlayBackStopped(self):
        logDebug("--> onPlayBackStopped")

        if self.CONTROLLING_LAMPS == 1:
            self._setState(self.savedlampstate)

        self.CONTROLLING_LAMPS = 0
        
        
    def onPlayBackPaused(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        logDebug("--> onPlayBackPaused")

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePaused")


    def onPlayBackResumed(self):
        __addon__ = xbmcaddon.Addon(id=self.addonId)
        logDebug("--> onPlayBackResumed")

        if self.CONTROLLING_LAMPS == 1:
            self._setScene("scenePlaying")




# Check if the bridge still exists where we expect it
__addon__ = xbmcaddon.Addon(id=xbmccommon.ADDON_ID)
__language__ = __addon__.getLocalizedString


hueAddonSettings = xbmccommon.HueControlSettings()
hueBridgeOk = False

# Make sure the important settings exist
if ("bridgeip" in hueAddonSettings.data and "bridgeid" in hueAddonSettings.data):
    bridge = hue.BridgeLocator(iprange=xbmc.getIPAddress()).FindBridgeById(hueAddonSettings.data["bridgeid"], hueAddonSettings.data["bridgeip"])
    
    if bridge == None:
        xbmccommon.notify(__language__(30019), duration=10000)
    else:
        bridge.username = hueAddonSettings.data.get("bridgeusername", None)
        bridge.devicetype = huecontrol.DEVICETYPE.format(xbmc.getInfoLabel('System.FriendlyName'))
        
        if not bridge.isAuthorized():
            xbmccommon.notify(__language__(30019), duration=10000)
        else:
            hueAddonSettings.data["bridgeip"] = bridge.ip
            hueAddonSettings.data["bridgeid"] = bridge.id
            
            if hueAddonSettings.store():
                xbmccommon.notify(__language__(30018))
                

            
            
huePlayer = HuePlayer()
monitor = xbmc.Monitor()
 
while not monitor.abortRequested():
    # Sleep/wait for abort for 10 seconds
    if monitor.waitForAbort(10):
        # Abort was requested while waiting. We should exit
        break
