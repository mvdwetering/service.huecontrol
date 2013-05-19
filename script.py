#
# XBMC Script plugin that handles the actions for the huecontorl
#

import json
import httplib
import xbmc, xbmcgui, xbmcaddon
import subprocess,os
import sys
from urlparse import urlparse, parse_qs
import pickle
import os
import errno

import hue
import huecontrol
import time


addonId = sys.argv[0]  # e.g.   service.huecontrol

__addon__ = xbmcaddon.Addon(id=huecontrol.ADDON_ID)
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonicon__ = os.path.join(__addonpath__, 'icon.png')
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

if (os.path.isfile(__addondatafile__)):
    with open(__addondatafile__, 'rb') as handle:
      hueAddonSettings = pickle.loads(handle.read())
      


idx = 1
parameters = {}
while idx < len(sys.argv):
    args = sys.argv[idx].split('=')
    parameters[args[0]] = args[1]
    idx += 1

if (not 'action' in parameters):
    # No action paramter, so must be run from programs thingy.
    # Lets show settings for now
    __addon__.openSettings()
    
elif (parameters['action'] == "connect_to_bridge"):
    
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
        huecontrol.notify(__language__(30011).format(bridge.name)) # Keep output on one line. Name is name + IP e.g. Philips hue (111.112.113.114)
    else:
        dialog = xbmcgui.Dialog()
        
        bridgenames = ["{0}, {1} ({2})".format(bridge.name, bridge.id, bridge.ip) for bridge in bridges]
        bridgeidx = dialog.select(__language__(30011), bridgenames)
    
    if (bridgeidx >= 0):
        bridge = bridges[bridgeidx]
        bridge.username = huecontrol.BRIDGEUSER
        bridge.devicetype = huecontrol.DEVICETYPE
        
        xbmc.log(msg='Selected bridge {0} = {1}'.format(bridgeidx, bridge))
        
        #__addon__.setSetting("bridgeip", bridge.ip)
        #__addon__.setSetting("bridgeid", bridge.id)
        hueAddonSettings["bridgeip"] = bridge.ip
        hueAddonSettings["bridgeid"] = bridge.id
        with open(__addondatafile__, 'wb') as handle:
            pickle.dump(hueAddonSettings, handle)

        
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
            huecontrol.notify(__language__(30016), duration=5000)
        else:
            huecontrol.notify(__language__(30017), duration=5000)
            
elif (parameters['action'] == "savescene"):
    
    bridge = hue.Bridge(ip=hueAddonSettings["bridgeip"], id=hueAddonSettings["bridgeid"], username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
    
    state = bridge.getFullState()
    #state = "asdfghjklasdfghjklasdfghjklasdfghjklasdfghjklasdfghjkl"

    id = parameters['id']
    #print("save scene" + id + ": " + str(state))
    __addon__.setSetting("scene" + id, str(state))
    huecontrol.notify("{0} lamp state stored".format(id))

elif (parameters['action'] == "recallscene"):

    id = parameters['id']
    state = __addon__.getSetting("scene" + id)
    print("recall scene" + id + ": " + state)

    bridge = hue.Bridge(ip=__addon__.getSetting("bridgeip"), id=__addon__.getSetting("bridgeid"), username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
    bridge.setFullStateLights(state)

    
    