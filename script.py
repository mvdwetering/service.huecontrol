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
import time


addonId = sys.argv[0]  # e.g.   service.huecontrol

hueAddon = xbmcaddon.Addon(id=huecontrol.ADDON_ID)

print "hueAddon",hueAddon
print hueAddon.getSetting("minvideolength")
#hueAddon.setSetting("minvideolength", "33")
print hueAddon.getSetting("bridgeip")
print "id",hueAddon.getSetting("bridgeid")

idx = 1
parameters = {}
while idx < len(sys.argv):
    args = sys.argv[idx].split('=')
    parameters[args[0]] = args[1]
    idx += 1

if (parameters['action'] == "connect_to_bridge"):
    
    progress = xbmcgui.DialogProgress()
    progress.create('Searching', 'Searching for hue bridge.')
    progress.update(0)
    
    bridges = hue.BridgeLocator().FindBridges(iprange=xbmc.getIPAddress() ,progress=progress.update)
    bridgeidx = -1;
    
    progress.close();
    
    if (len(bridges) == 0):
        xbmcgui.Dialog().ok("Search failed", "Could not locate a hue bridge :-(") 
    elif (len(bridges) == 1):
        # Only one bridge, done
        bridgeidx = 0
        bridge = bridges[bridgeidx]
        xbmc.executebuiltin('Notification("Found hue bridge", "{0}\n{1}({2})", 2000)'.format(bridge.name, bridge.id, bridge.ip))
    else:
        dialog = xbmcgui.Dialog()
        
        bridgenames = ["{0}, {1} ({2})".format(bridge.name, bridge.id, bridge.ip) for bridge in bridges]
        bridgeidx = dialog.select('Select a bridge', bridgenames)
    
    if (bridgeidx >= 0):
        bridge = bridges[bridgeidx]
        bridge.username = huecontrol.BRIDGEUSER
        bridge.devicetype = huecontrol.DEVICETYPE
        
        xbmc.log(msg='Selected bridge {0} = {1}'.format(bridgeidx, bridge))
        
        hueAddon.setSetting("bridgeip", bridge.ip)
        hueAddon.setSetting("bridgeid", bridge.id)
        
        if (not bridge.isAuthorized()):
            # Perform authorization part
            # Use progress dialog to have a button with a cancel button
            progress = xbmcgui.DialogProgress()
            progress.create('Authorizing', 'Press the button on the bridge')
            progress.update(0)
            
            maxcount = 60
            count = 0
            while count < maxcount:
                time.sleep(1)
                
                result = bridge.authorize()
                
                if result == 0 or progress.iscanceled():
                    # done, break loop
                    count = maxcount
                
                progress.update((100/maxcount) * count, "Press the button on the bridge\n{0} seconds remaining".format(maxcount - count))
                #print("{0} seconds remaining".format(maxcount - count))
                
                count = count + 1
                
            progress.close();
            
        if (not bridge.isAuthorized()):
            xbmc.executebuiltin('Notification("Authorization","Authorization failed.\nPlease try again.",5000)')
        else:
            xbmc.executebuiltin('Notification("hue control","Authorized and ready to rock",5000)')
            
elif (parameters['action'] == "savescene"):
    
    bridge = hue.Bridge(ip=hueAddon.getSetting("bridgeip"), id=hueAddon.getSetting("bridgeid"), username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
    
    print "bridge", bridge
    
    state = bridge.getFullState()
    #state = "asdfghjklasdfghjklasdfghjklasdfghjklasdfghjklasdfghjkl"

    id = parameters['id']
    print("save scene" + id + ": " + str(state))
    hueAddon.setSetting("scene" + id, str(state))
    state2 = hueAddon.getSetting("scene" + id)
    print("save scene" + id + ": " + state2)
    xbmc.executebuiltin('Notification("hue control","Stored lamp state",2500)')

elif (parameters['action'] == "recallscene"):

    id = parameters['id']
    state = hueAddon.getSetting("scene" + id)
    print("recall scene" + id + ": " + state)

    bridge = hue.Bridge(ip=hueAddon.getSetting("bridgeip"), id=hueAddon.getSetting("bridgeid"), username=huecontrol.BRIDGEUSER, devicetype=huecontrol.DEVICETYPE)
    bridge.setFullStateLights(state)
    #bridge.setFullStateLights('{"lights":{"1":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 1", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"2":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 2", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"3":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 3", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"4":{"state": {"on":true,"bri":218,"hue":12846,"sat":250,"xy":[0.6484,0.3309],"ct":358,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Kamer", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"5":{"state": {"on":true,"bri":218,"hue":13857,"sat":250,"xy":[0.6484,0.3309],"ct":500,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Achter", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"6":{"state": {"on":true,"bri":218,"hue":19581,"sat":250,"xy":[0.6484,0.3309],"ct":281,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Bol", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"7":{"state": {"on":false,"bri":0,"hue":41234,"sat":3,"xy":[0.4316,0.4025],"ct":325,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Hal", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"8":{"state": {"on":false,"bri":0,"hue":12879,"sat":56,"xy":[0.4594,0.4127],"ct":370,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Slaapkamer", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"9":{"state": {"on":true,"bri":254,"hue":12879,"sat":56,"xy":[0.4594,0.4127],"ct":370,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Zolder", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }}},"groups":{"1":{"action": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"effect":"none","colormode":"ct"},"lights":["1","2","3"],"name": "Eettafel"},"2":{"action": {"on":true,"bri":218,"hue":19581,"sat":250,"xy":[0.6484,0.3309],"ct":281,"effect":"none","colormode":"ct"},"lights":["1","2","3","4","5","6"],"name": "Kamer + Bol"}},"config":{"name": "My round bridge","mac": "00:17:88:09:a0:e5","dhcp": true,"ipaddress": "192.168.178.28","netmask": "255.255.255.0","gateway": "192.168.178.1","proxyaddress": "none","proxyport": 0,"UTC": "2013-02-26T20:26:16","whitelist":{"aValidUser":{"last use date": "2013-02-26T20:26:15","create date": "2012-09-25T11:39:43","name": "CLIP API Debugger"},"fffffffff6043c293eab2960768d2d20":{"last use date": "2012-11-02T07:08:57","create date": "2012-10-08T18:18:51","name": "samsung GT-S5360"},"000000003159210c0033c5870033c587":{"last use date": "2012-11-05T17:28:52","create date": "2012-10-11T20:36:56","name": "asus ASUS Transformer Pad TF300T"},"955a43c5cb5480e10c2bc61c31c70a4d":{"last use date": "2012-10-25T06:13:32","create date": "2012-10-16T18:09:28","name": "iPod touch"},"ffffffffff7a64322307d72a0033c587":{"last use date": "2012-11-02T18:02:46","create date": "2012-11-02T17:53:55","name": "Sony Sony Tablet S"},"ffffffffff7a643272869bf272869bf2":{"last use date": "2012-12-11T19:30:42","create date": "2012-11-02T19:06:53","name": "Sony Tablet S"},"fffffffff6043c297df7ed317df7ed31":{"last use date": "2013-02-26T20:26:12","create date": "2012-11-02T19:17:21","name": "samsung GT-S5360"},"000000003159210cffffffffbafeea87":{"last use date": "1911-10-26T21:49:19","create date": "2012-11-05T17:58:49","name": "asus ASUS Transformer Pad TF300T"},"65c3f3f7caf6f3c782a5cf3ed8b25de2c83e5b07":{"last use date": "2013-02-26T19:06:23","create date": "2012-11-25T20:48:26","name": "CoolDeviceName"}},"swversion": "00005128","swupdate":{"updatestate":0,"url":"","text":"","notify": false},"linkbutton": false,"portalservices": true},"schedules":{}}')
        
#        xbmc.log(msg='This is a test string.')
#        xbmc.executebuiltin('Notification("Header","message",2000)')
    
xbmc.log(msg='This is a test string 2222.')

    

 

    