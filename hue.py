#
# Code to controll the hue bridge
#

import json
import httplib
import traceback
from datetime import datetime
from xml.dom import minidom
from threading import Lock
from threading import Thread
from Queue import Queue
import socket
import time
import re
import sys

MAX_LAMPS = 50
NUM_THREADS = 20

class BridgeLocator:
    '''Class that finds hue bridges in the network'''
    bridges = []
    lock = Lock()
    q = Queue()

    
    def FindBridgeTask(self):
        done = False
        while not done:
            item = self.q.get()
#            print(item)
            sys.stdout.write('.')
            if item == "STOP":
                done = True
            else:
                bridge = self.GetBridgeFromIp(item)
                if bridge:
                    with self.lock:
                        self.bridges.append(bridge)
            self.q.task_done()

    def SearchIpRange(self, ip):
        print(ip)
        tmp = ip.rfind('.')
        ipstart = ip[0:tmp]
        #print(ipstart)
        for i in range(1,254):
            #ip = "192.168.178.{0}".format(i)
            #print(ipstart,i)
            self.q.put("{0}.{1}".format(ipstart, i))
        
    def FindBridges(self, progress=None, iprange=None):
        '''Crude first implementation, just try all addresses in the subnet'''
        self.bridges = []
        
        for i in range(NUM_THREADS):
            t = Thread(target=self.FindBridgeTask)
            t.daemon = True
            t.start()

        rangecount = 0

        if (iprange is None):
            for ipaddress in [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.0.0.")]: # magic from the internet (works on my windows, not on OpenElec)
            
                # Only spam valid home addres ranges
                
                # 10.0.0.0 through 10.255.255.255
                # 169.254.0.0 through 169.254.255.255 (Autoip)
                # 172.16.0.0 through 172.31.255.255
                # 192.168.0.0 through 192.168.255.255 
                if (not re.match("^127\.\d{123}\.\d{123}\.\d{123}$", ip) and 
                    not re.match("^10\.\d{123}\.\d{123}\.\d{123}$", ip) and 
                    not re.match("^192\.168.\d{123}$", ip) and 
                    not re.match("^172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{123}\.[0-9]{123}$", ip) ):
                    self.SearchIpRange(ipaddress)
                    rangecount += 1
        else:
            self.SearchIpRange(iprange)
            rangecount = 1
        
        if (not progress is None):
            numitemstotal = rangecount * 254

            while (not self.q.empty()):
                numitemsleft = self.q.qsize()
                percent = ((numitemstotal - numitemsleft) / float(numitemstotal)) * 100
                progress(int(percent))
                #print("{0} {1} {2}".format(numitemstotal,(numitemstotal - numitemsleft),percent))
                time.sleep(0.3)
        
            progress(100)    # Done ;-)

        self.q.join()
        
        # Done with the threads, time to close them down, otherwise they hang xbmc when tying to close it
        for i in range(NUM_THREADS):
            self.q.put("STOP")
        
        return self.bridges    


    def GetBridgeFromIp(self, ip):
        #print(ip)
        bridge = None
        try:
            conn = httplib.HTTPConnection(ip, timeout=1)
            conn.request("GET", '/description.xml') 
            resp = conn.getresponse()  # Ignore response for now, assume it all went OK
            
            if (resp.status == 200):
                # Found a description.xml. Parse it to get the bridge ID (and name)
                xmldata = ""
                chunk = True

                while chunk:
                    chunk = resp.read()
                    xmldata += chunk

                xmldoc = minidom.parseString(xmldata)  
                
                devicenode = xmldoc.getElementsByTagName("device")[0]
                serial = devicenode.getElementsByTagName("serialNumber")[0].childNodes[0].data
                friendlyname = devicenode.getElementsByTagName("friendlyName")[0].childNodes[0].data
                
                bridge = Bridge(ip, serial, friendlyname)

            conn.close()
            
        except Exception as e:
            #print str(datetime.now()), "An error occured!"
            #traceback.print_exc()
            pass
    
        return bridge
                
        
    def FindBridgeById(self, bridgeid, lastip=None, iprange=None):
        # TODO, make it fast when no IP provided. Then stop when found.
        
        # Try last known IP if provided
        if lastip:
            bridge = self.GetBridgeFromIp(lastip)
            if bridge and bridge.id == bridgeid:
                return bridge;
                
        # Otherwise just find all and filter.
        bridges = self.FindBridges(iprange=iprange)
        
        for bridge in bridges:
            if bridge.id == bridgeid:
                return bridge;
        
        return None


class Bridge:
    '''Represents the bridge, use it to control the lights'''
    ip = 0
    id = 0
    name = "Philips hue"
    username = None
    devicetype = None
    authorized = False
    
    authorizeThread = None
    authorizeDuration = 0;

    
    def __init__(self, ip=None, id=None, name=None, devicetype=None, username=None):
        self.ip = ip
        self.id = id
        self.name = name
        self.devicetype = devicetype
        self.username = username

    def __repr__(self):
        return "{0} - {1} - {2}".format(self.name, self.id, self.ip)
        

    def authorize(self):
        # Attempt to create the user
        data = {'username':self.username, 'devicetype':self.devicetype}
        jsonstr = json.dumps(data)

        conn = httplib.HTTPConnection(self.ip)
        conn.request("POST", '/api', jsonstr) 
        resp = conn.getresponse()
        data = resp.read()
        
        reply = json.loads(data)[0]
        conn.close()  
#        print data
#        print(reply)
        
        if ('success' in reply):
            return 0
        elif ('error' in reply):
            return reply['error']['type']
        else:
            # Something weird happend
            return 666
        
    def isAuthorized(self):
        # Just get teh config and check for something in there
        conn = httplib.HTTPConnection(self.ip)
        conn.request("GET", '/api/{0}/config'.format(self.username), "") 
        resp = conn.getresponse()
        data = resp.read()
        #print data
        reply = json.loads(data)
        conn.close()  
#        print data
#        print(reply)
        
        if ('whitelist' in reply):
            return 1

        return 0

    def getFullState(self):
        # Get the full state of the bridge
        conn = httplib.HTTPConnection(self.ip)
        conn.request("GET", '/api/{0}'.format(self.username), "") 
        resp = conn.getresponse()
        data = resp.read()
        #print data
        reply = json.loads(data)
        conn.close()  
#        print data
#        print(reply)
        
        return data  # return the string so the receiver can easily store it (relevant for saving settings in XBMC which must be strings)
        
    def setFullStateLights(self, state, lightList=None, briOnly=False):
    
        # Set the lights back to the given full state of the bridge
        if isinstance(state, basestring):
            parsedjson = json.loads(state)
        else:
            parsedjson = state
        
        lights = parsedjson['lights']
        #print(lights)

        for i in range(MAX_LAMPS):
            strId = str(i)
            #print(strId)
            
#            if  (hueAddon.getSetting("lamp" + strId ) == "true"):
            if  not lightList or i in lightList:
                #print(strId)

                if (strId in lights):
                    storedstate = lights[strId]['state']
                    #print(strId, storedstate)

                    lampstate = {}
                    xsw = storedstate['on']
                    lampstate['on'] = xsw
                    lampstate['bri'] = storedstate['bri']
                    
                    if not briOnly:
                        # Also restore color stuff
                        if (storedstate['colormode'] == 'ct'):
                            lampstate['ct'] = storedstate['ct']
                        elif (storedstate['colormode'] == 'xy'):
                            lampstate['xy'] = storedstate['xy']
                        elif (storedstate['colormode'] == 'hs'):
                            lampstate['hue'] = storedstate['hue']
                            lampstate['sat'] = storedstate['sat']

                    #print(strId + ":" + json.dumps(lampstate))
                    self.sendLightState(i, json.dumps(lampstate))

        
    def sendLightState(self, id, json):
        conn = httplib.HTTPConnection(self.ip)
        conn.request("PUT", '/api/{0}/lights/{1}/state'.format(self.username, id), json) 
        print("PUT", '/api/{0}/lights/{1}/state'.format(self.username, id), json) 
        resp = conn.getresponse()  # Ignore response for now, assume it all went OK
        data = resp.read()
        #print data
        conn.close()

    def sendGroupAction(self, id, json):
        conn = httplib.HTTPConnection(self.ip)
        conn.request("PUT", '/api/{0}/groups/{1}/action'.format(self.username, id), json) 
        print('/api/{0}/groups/{1}/action'.format(self.username, id))
        resp = conn.getresponse()  # Ignore response for now, assume it all went OK
        data = resp.read()
        #print data
        conn.close()
        
    def setLightOn(self, id):
        self.sendLightState(self, id, '{"on": true}')
      
    def setLightOff(self, id):
        self.sendLightState(id, '{"on": false}')
      
    def setLightBri(self, id, bri):
        data = {'bri':int(bri), 'transitiontime': 20 }
        self.sendLightState(id, json.dumps(data))
        
    def setGroupBri(self, id, bri):
        data = {'bri':int(bri), 'transitiontime': 0 }
        self.sendGroupAction(id, json.dumps(data))
        
    def setGroupAlert(self, id):
        data = {'alert':'select'}
        self.sendGroupAction(id, json.dumps(data))

    
  
 

    