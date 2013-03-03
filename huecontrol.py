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
import time

ADDON_ID = 'service.huecontrol'

BRIDGEUSER = "65c3f3f7caf6f3c782a5cf3ed8b25de2c83e5b07"
DEVICETYPE = "XBMC hue control"

# NOTE: The huge amount of getting new addond references is to get the new settings
#       it seems that this reference is not updated when user changes settings
hueAddon = xbmcaddon.Addon(id=ADDON_ID)

BRIDGEUSER = "aValidUser"

MAX_LAMPS = 10

pluginUrl = sys.argv[0]             # e.g.   plugin://service.huecontrol/



def sendLightState(id, json):
    hueAddon = xbmcaddon.Addon(id=ADDON_ID)

    bridge_ip = hueAddon.getSetting("bridgeip")
    
    conn = httplib.HTTPConnection(bridge_ip)
    conn.request("PUT", '/api/'+ BRIDGEUSER +'/lights/' + str(id) + '/state', json) 
    resp = conn.getresponse()  # Ignore response for now, assume it all went OK
    data = resp.read()
    print data
    conn.close()

def getBridgeState():
    hueAddon = xbmcaddon.Addon(id=ADDON_ID)

    bridge_ip = hueAddon.getSetting("bridgeip")
    
    conn = httplib.HTTPConnection(bridge_ip)
    conn.request("GET", '/api/'+ BRIDGEUSER) 
    resp = conn.getresponse()  # Ignore response for now, assume it all went OK
    data = resp.read()
    print data
    conn.close()
    
    return data

def setBridgeState(state, briOnly=False):
    hueAddon = xbmcaddon.Addon(id=ADDON_ID)

    parsedjson = json.loads(state)
    lights = parsedjson['lights']
    print(lights)

    for i in range(MAX_LAMPS):
        strId = str(i)
        print(strId)
        if  (hueAddon.getSetting("lamp" + strId ) == "true"):
            print(strId)

            if (strId in lights):
                storedstate = lights[strId]['state']
                print(strId, storedstate)

                lampstate = {}
                xsw = storedstate['on']
                lampstate['on'] = xsw
                lampstate['bri'] = storedstate['bri']
                
                if (not briOnly):
                    # Also restore color stuff
                    if (storedstate['colormode'] == 'ct'):
                        lampstate['ct'] = storedstate['ct']
                    elif (storedstate['colormode'] == 'xy'):
                        lampstate['xy'] = storedstate['xy']
                    elif (storedstate['colormode'] == 'hs'):
                        lampstate['hue'] = storedstate['hue']
                        lampstate['sat'] = storedstate['sat']

                print(strId + ":" + json.dumps(lampstate))
                sendLightState(i, json.dumps(lampstate))

def setLightOn(id):
    sendLightState(id, '{"on": true}')
  
def setLightOff(id):
    sendLightState(id, '{"on": false}')
  
def setLightBri(id, bri):
    data = {'bri':int(bri), 'transitiontime': 20 }
    sendLightState(id, json.dumps(data))

    
  
class HuePlayer(xbmc.Player):

    def __init__ (self):
        xbmc.Player.__init__(self)
        
        self.savedlampstate = '{"lights":{}}'
        self.CONTROLLING_LAMPS = 0
        self.addonId = 'service.huecontrol'

        print "--> Init"

    def onPlayBackStarted(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)

        print "--> onPlayBackStarted"
        print xbmc.Player().getTotalTime()
        print hueAddon.getSetting("minvideolength")

        if xbmc.Player().isPlayingVideo() and xbmc.Player().getTotalTime() >= (float(hueAddon.getSetting("minvideolength")) * 60):
            if (self.CONTROLLING_LAMPS == 0):
                self.savedlampstate = getBridgeState()

            self.CONTROLLING_LAMPS = 1
            setBridgeState(hueAddon.getSetting("scenePlaying"), hueAddon.getSetting("brightnessonlyscenePlaying") == "true")
            
    def onPlayBackEnded(self):
        print "--> onPlayBackEnded"
        print xbmc.Player().getTotalTime()
            
        if self.CONTROLLING_LAMPS == 1:
            setBridgeState(self.savedlampstate)
            
        self.CONTROLLING_LAMPS = 0

    def onPlayBackStopped(self):
        print "--> onPlayBackStopped"

        if self.CONTROLLING_LAMPS == 1:
            setBridgeState(self.savedlampstate)

        self.CONTROLLING_LAMPS = 0
        
        
    def onPlayBackPaused(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackPaused"
        print xbmc.Player().getTotalTime()

        if self.CONTROLLING_LAMPS == 1:
            setBridgeState(hueAddon.getSetting("scenePaused"), hueAddon.getSetting("brightnessonlyscenePaused") == "true")


    def onPlayBackResumed(self):
        hueAddon = xbmcaddon.Addon(id=self.addonId)
        print "--> onPlayBackResumed"
        print xbmc.Player().getTotalTime()

        if self.CONTROLLING_LAMPS == 1:
            setBridgeState(hueAddon.getSetting("scenePlaying"), hueAddon.getSetting("brightnessonlyscenePlaying") == "true")



if (len(sys.argv) >= 2):
    # Trigger an action mode
    pluginHandle = int(sys.argv[1])
    parameters = parse_qs(urlparse(sys.argv[2]).query)

    if (parameters['action'][0] == "connect_to_bridge"):
        
        progress = xbmcgui.DialogProgress()
        progress.create('Searching', 'Searching for hue bridge.')
        progress.update(0)   # hides progressbar TODO: Find some way to add progress
        
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
            xbmc.log(msg='Selected bridge {0} = {1}'.format(bridgeidx, bridge))
            
            hueAddon.setSetting("bridgeip", bridge.ip)
            hueAddon.setSetting("bridgeid", bridge.id)
            
            if (not bridge.isAuthorized(BRIDGEUSER)):
                # Perform authorization part
                # Use progress dialog to have a button with a cancel button
                progress = xbmcgui.DialogProgress()
                progress.create('Authorizing', 'Press the button on the bridge')
                progress.update(0)   # hides (according to docs anyways...) progressbar TODO: Find some way to add progress
                
                maxcount = 60
                count = 0
                while count < maxcount:
                    time.sleep(1)
                    
                    result = bridge.authorize(DEVICETYPE, BRIDGEUSER)
                    
                    if result == 0 or progress.iscanceled():
                        # done, break loop
                        count = maxcount
                    
                    progress.update((100/maxcount) * count, "Press the button on the bridge\n{0} seconds remaining".format(maxcount - count))
                    #print("{0} seconds remaining".format(maxcount - count))
                    
                    count = count + 1
                    
                progress.close();
                
            if (not bridge.isAuthorized(BRIDGEUSER)):
                xbmc.executebuiltin('Notification("Authorization","Authorization failed.\nPlease try again.",5000)')
            else:
                xbmc.executebuiltin('Notification("hue control","Authorized and ready to rock",5000)')
                
    elif (parameters['action'][0] == "savescene"):
        id = parameters['id'][0]
        state = getBridgeState()
        #state = "asdfghjklasdfghjklasdfghjklasdfghjklasdfghjklasdfghjkl"
        print("save scene" + id + ": " + state)
        hueAddon.setSetting("scene" + id, state)
        state2 = hueAddon.getSetting("scene" + id)
        print("save scene" + id + ": " + state2)
        xbmc.executebuiltin('Notification("hue control","Stored lamp state",2500)')

    elif (parameters['action'][0] == "recallscene"):
        id = parameters['id'][0]
        state = hueAddon.getSetting("scene" + id)
        print("recall scene" + id + ": " + state)
        setBridgeState(state)
        #setBridgeState('{"lights":{"1":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 1", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"2":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 2", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"3":{"state": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Eettafel 3", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"4":{"state": {"on":true,"bri":218,"hue":12846,"sat":250,"xy":[0.6484,0.3309],"ct":358,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Kamer", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"5":{"state": {"on":true,"bri":218,"hue":13857,"sat":250,"xy":[0.6484,0.3309],"ct":500,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Achter", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"6":{"state": {"on":true,"bri":218,"hue":19581,"sat":250,"xy":[0.6484,0.3309],"ct":281,"alert":"none","effect":"none","colormode":"xy","reachable":true}, "type": "Extended color light", "name": "Bol", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"7":{"state": {"on":false,"bri":0,"hue":41234,"sat":3,"xy":[0.4316,0.4025],"ct":325,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Hal", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"8":{"state": {"on":false,"bri":0,"hue":12879,"sat":56,"xy":[0.4594,0.4127],"ct":370,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Slaapkamer", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }},"9":{"state": {"on":true,"bri":254,"hue":12879,"sat":56,"xy":[0.4594,0.4127],"ct":370,"alert":"none","effect":"none","colormode":"ct","reachable":true}, "type": "Extended color light", "name": "Zolder", "modelid": "LLC008", "swversion": "3.1.0.0000", "pointsymbol": { "1":"320000002a7f000000ff00000000000000000000", "2":"320000002a007f0000ff00000000000000000000", "3":"320000002a00007f00ff00000000000000000000", "4":"140000003f30730000ff00000000000000000000", "5":"none", "6":"none", "7":"none", "8":"none" }}},"groups":{"1":{"action": {"on":true,"bri":218,"hue":12879,"sat":56,"xy":[0.6484,0.3309],"ct":342,"effect":"none","colormode":"ct"},"lights":["1","2","3"],"name": "Eettafel"},"2":{"action": {"on":true,"bri":218,"hue":19581,"sat":250,"xy":[0.6484,0.3309],"ct":281,"effect":"none","colormode":"ct"},"lights":["1","2","3","4","5","6"],"name": "Kamer + Bol"}},"config":{"name": "My round bridge","mac": "00:17:88:09:a0:e5","dhcp": true,"ipaddress": "192.168.178.28","netmask": "255.255.255.0","gateway": "192.168.178.1","proxyaddress": "none","proxyport": 0,"UTC": "2013-02-26T20:26:16","whitelist":{"aValidUser":{"last use date": "2013-02-26T20:26:15","create date": "2012-09-25T11:39:43","name": "CLIP API Debugger"},"fffffffff6043c293eab2960768d2d20":{"last use date": "2012-11-02T07:08:57","create date": "2012-10-08T18:18:51","name": "samsung GT-S5360"},"000000003159210c0033c5870033c587":{"last use date": "2012-11-05T17:28:52","create date": "2012-10-11T20:36:56","name": "asus ASUS Transformer Pad TF300T"},"955a43c5cb5480e10c2bc61c31c70a4d":{"last use date": "2012-10-25T06:13:32","create date": "2012-10-16T18:09:28","name": "iPod touch"},"ffffffffff7a64322307d72a0033c587":{"last use date": "2012-11-02T18:02:46","create date": "2012-11-02T17:53:55","name": "Sony Sony Tablet S"},"ffffffffff7a643272869bf272869bf2":{"last use date": "2012-12-11T19:30:42","create date": "2012-11-02T19:06:53","name": "Sony Tablet S"},"fffffffff6043c297df7ed317df7ed31":{"last use date": "2013-02-26T20:26:12","create date": "2012-11-02T19:17:21","name": "samsung GT-S5360"},"000000003159210cffffffffbafeea87":{"last use date": "1911-10-26T21:49:19","create date": "2012-11-05T17:58:49","name": "asus ASUS Transformer Pad TF300T"},"65c3f3f7caf6f3c782a5cf3ed8b25de2c83e5b07":{"last use date": "2013-02-26T19:06:23","create date": "2012-11-25T20:48:26","name": "CoolDeviceName"}},"swversion": "00005128","swupdate":{"updatestate":0,"url":"","text":"","notify": false},"linkbutton": false,"portalservices": true},"schedules":{}}')
        
#        xbmc.log(msg='This is a test string.')
#        xbmc.executebuiltin('Notification("Header","message",2000)')
    
    xbmc.log(msg='This is a test string 2222.')
else:
    # Service mode
    huePlayer = HuePlayer()
    
    while(not xbmc.abortRequested):
        # Getting new reference to the addon, this will also make sure the settings are reloaded so changes
        # throught the settings UI are used. Otherwise the service will keep having the settings from when the service was started
        # TODO: see if this can be made better, this is just silly
        ##hueAddon = xbmcaddon.Addon(id='service.huecontrol')
        #print "Loopy"
        xbmc.sleep(1000)

 

    