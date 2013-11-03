#
# XBMC Script plugin that handles the actions for the huecontorl
#

import json
import httplib
import xbmc, xbmcgui, xbmcaddon
import subprocess,os
import sys
from urlparse import urlparse, parse_qs

import hue
import huecontrol
import xbmccommon
import time


addonId = sys.argv[0]  # e.g.   service.huecontrol

__addon__ = xbmcaddon.Addon(id=xbmccommon.ADDON_ID)
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonicon__ = os.path.join(__addonpath__, 'icon.png')
__language__ = __addon__.getLocalizedString


hueAddonSettings = xbmccommon.HueControlSettings()

idx = 1
parameters = {}
parameters["action"] = "none"

while idx < len(sys.argv):
    args = sys.argv[idx].split('=')
    parameters[args[0]] = args[1]
    idx += 1

if (parameters['action'] == "none"):
    # No action paramter, so must be run from programs thingy.
    # Lets show settings for now
    #__addon__.openSettings()
    parameters['action'] = "showpresets"


    
if (parameters['action'] == "connect_to_bridge"):
    
    progress = xbmcgui.DialogProgress()
    progress.create(__language__(30007), __language__(30008))
    progress.update(0)
    
    bridges = hue.BridgeLocator(iprange=xbmc.getIPAddress()).FindBridges(progress=progress.update)
    bridgeidx = -1;
    
    progress.close();
    
    if (len(bridges) == 0):
        xbmcgui.Dialog().ok(__language__(30009), __language__(30010)) 
    elif (len(bridges) == 1):
        # Only one bridge, done
        bridgeidx = 0
        bridge = bridges[bridgeidx]
        xbmccommon.notify(__language__(30011).format(bridge.name)) # Keep output on one line. Name is name + IP e.g. Philips hue (111.112.113.114)
    else:
        dialog = xbmcgui.Dialog()
        
        bridgenames = ["{0}, {1} ({2})".format(bridge.name, bridge.id, bridge.ip) for bridge in bridges]
        bridgeidx = dialog.select(__language__(30011), bridgenames)
    
    if (bridgeidx >= 0):
        bridge = bridges[bridgeidx]
        if ("bridgeusername" in hueAddonSettings.data):
            bridge.username = hueAddonSettings.data["bridgeusername"]
        bridge.devicetype = huecontrol.DEVICETYPE.format(xbmc.getInfoLabel('System.FriendlyName') )
        
        xbmc.log(msg='Selected bridge {0} = {1}'.format(bridgeidx, bridge))
        
        hueAddonSettings.data["bridgeip"] = bridge.ip
        hueAddonSettings.data["bridgeid"] = bridge.id
        
        if (not bridge.isAuthorized()):
            # Perform authorization part
            # Use progress dialog to have a button with a cancel button
            progress = xbmcgui.DialogProgress()
            progress.create(__language__(30013), __language__(30014))
            progress.update(0)
            
            maxcount = 60
            count = 0
            while count < maxcount:
                progress.update(int((100.0/maxcount) * count), (__language__(30014) + "\n" + __language__(30015)).format(maxcount - count))
                #print("{0} seconds remaining".format(maxcount - count))

                result = bridge.authorize()
                
                if result == 0 or progress.iscanceled():
                    # done, break loop
                    count = maxcount
                
                count = count + 1
                time.sleep(1)
                
            progress.close();
            
        if (not bridge.isAuthorized()):
            xbmccommon.notify(__language__(30016), duration=5000)
        else:
            hueAddonSettings.data["bridgeusername"] = bridge.username
            # For safety remove any old (fixed) usernames
            bridge.DELETE("/config/whitelist/{0}".format(huecontrol.OLD_BRIDGEUSER))
            
            xbmccommon.notify(__language__(30017), duration=5000)
            
        hueAddonSettings.store()
    
elif (parameters['action'] == "savescene"):
    
    bridge = hue.Bridge(ip=hueAddonSettings.data["bridgeip"], id=hueAddonSettings.data["bridgeid"], username=hueAddonSettings.data.get("bridgeusername", None))
    
    state = bridge.getFullState()
    #state = "asdfghjklasdfghjklasdfghjklasdfghjklasdfghjklasdfghjkl"

    id = parameters['id']
    #print("save scene" + id + ": " + str(state))
    __addon__.setSetting("scene" + id, str(state))
    hueAddonSettings.data["scene" + id] = state
    
    if hueAddonSettings.store():
        #if (__addon__.getSetting("namescene" + id)):
        #    id = __language__(id)
        xbmccommon.notify(__language__(30034).format(id))

elif (parameters['action'] == "recallscene"):

    id = parameters['id']
    #state = __addon__.getSetting("scene" + id)
    state = hueAddonSettings.data["scene" + id]
    print("recall scene" + id + ": " + str(state))

    bridge = hue.Bridge(ip=hueAddonSettings.data["bridgeip"], id=hueAddonSettings.data["bridgeid"], username=hueAddonSettings.data.get("bridgeusername", None))
    bridge.setFullStateLights(state)

elif (parameters['action'] == "showpresets"):

    dialog = xbmcgui.Dialog()
    
    presetnames = []
    
    presetnames.append(__language__(30030))  # Playing
    presetnames.append(__language__(30040))  # Paused
    
    for i in range(huecontrol.NUM_PRESETS):
        presetnames.append (__addon__.getSetting("namescenePreset" + str(i+1)))
        print "namescene" + str(i+1) + " - " +  __addon__.getSetting("namescenePreset" + str(i+1))
    
    idx = dialog.select(__language__(30202), presetnames)
    
    if idx >= 0:
        # Assume one of the presets
        presetId = "Preset" + str(idx+1-2)
        
        if idx == 0:
            presetId = "Playing"
        if idx == 1:
            presetId = "Paused"

        #state = __addon__.getSetting("scene" + presetId)
        state = hueAddonSettings.data["scene" + presetId]
        print("recall preset" + presetId + ": " + str(state))

        bridge = hue.Bridge(ip=hueAddonSettings.data["bridgeip"], id=hueAddonSettings.data["bridgeid"],username=hueAddonSettings.data.get("bridgeusername", None))
        bridge.setFullStateLights(state)

    
