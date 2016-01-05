#
# Code to control the hue bridge
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

MAX_LAMPS = 63   # Max lamps supported by the bridge
NUM_THREADS = 20 # Number of threads spawned when searching the network for bridges

class BridgeLocator:
    '''Class that finds hue bridges in the network'''
    bridges = []
    lock = Lock()
    q = Queue()

    def __init__(self, iprange=None):
        self.iprange = iprange

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

    def SearchIpRange(self, iprange=None):
    
        if iprange == None:
            iprange = self.iprange;

        print(iprange)
        tmp = iprange.rfind('.')
        ipstart = iprange[0:tmp]
        #print(ipstart)
        for i in range(1,254):
            #self.iprange = "192.168.178.{0}".format(i)
            #print(ipstart,i)
            self.q.put("{0}.{1}".format(ipstart, i))
        
    def FindBridges(self, progress=None):
        '''Crude first implementation, just try all addresses in the subnet'''
        self.bridges = []
        
        for i in range(NUM_THREADS):
            t = Thread(target=self.FindBridgeTask)
            t.daemon = True
            t.start()

        rangecount = 0

        if (self.iprange is None):
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
            self.SearchIpRange()
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
        
        # Done with the threads, time to close them down, otherwise they hang Kodi when tying to close it
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
                
        
    def FindBridgeById(self, bridgeid, lastip=None):
        # TODO, make it fast when no IP provided. Then stop when found.
        
        # Try last known IP if provided
        if lastip:
            bridge = self.GetBridgeFromIp(lastip)
            if bridge and bridge.id == bridgeid:
                return bridge;
                
        # Otherwise just find all and filter.
        bridges = self.FindBridges()
        
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
    

    def __init__(self, ip=None, id=None, name=None, devicetype=None, username=None, logfunc=None):
        self.ip = ip
        self.id = id
        self.name = name
        self.devicetype = devicetype
        self.username = username
        self.logfunc = logfunc

    def __repr__(self):
        return "{0} - {1} - {2}".format(self.name, self.id, self.ip)
        

    def authorize(self):
        # Attempt to create the/a user
        data = {'devicetype':self.devicetype}
        if (self.username):
            data['username'] = self.username,
        
        #jsonstr = json.dumps(data)
        reply = self.POST("", data, addUsername=False)
        
        if ('success' in reply[0]):
            self.username = reply[0]["success"]["username"]  # Will be random name or the one provided
            return 0
        elif ('error' in reply[0]):
            return reply[0]['error']['type']
        else:
            # Something weird happend
            return 666
        
    def isAuthorized(self):
        # Just get the config and check if we can see the whitelist
        reply = self.GET("/config")
        
        if ('whitelist' in reply):
            return 1

        return 0

    def getFullState(self):
        # Get the full state of the bridge
        reply = self.GET("")

        return json.dumps(reply)  # return the string so the receiver can easily store it (relevant for saving settings in Kodi which must be strings)
        
    def setFullStateLights(self, state, lightList=None, briOnly=False):
    
        # Set the lights back to the given full state of the bridge
        if isinstance(state, basestring):
            # Dont apply empty states
            if state == "":
                return
            parsedjson = json.loads(state)
        else:
            parsedjson = state
        
        if not 'lights' in parsedjson:
            return
            
        lights = parsedjson['lights']
        #print(lights)

        for i in range(MAX_LAMPS):
            strId = str(i)
            #print(strId)
            
            if  not lightList or (i in lightList):
                #print(strId)

                if (strId in lights):
                    storedstate = lights[strId]['state']
                    #print(strId, storedstate)

                    lampstate = {}

                    lampstate['on'] = storedstate['on']
                    
                    # When lamp going to be off don't send the rest
                    # It avoids weird color flash
                    if storedstate['on'] != False:
                        lampstate['bri'] = storedstate['bri']
                        
                        if not briOnly:
                            # Also restore color stuff if available (e.g. living whites do not have colormode)
                            if 'colormode' in storedstate:
                                if (storedstate['colormode'] == 'ct'):
                                    lampstate['ct'] = storedstate['ct']
                                elif (storedstate['colormode'] == 'xy'):
                                    lampstate['xy'] = storedstate['xy']
                                elif (storedstate['colormode'] == 'hs'):
                                    lampstate['hue'] = storedstate['hue']
                                    lampstate['sat'] = storedstate['sat']

                    #print(strId + ":" + json.dumps(lampstate))
                    self.PUT('/lights/{0}/state'.format(strId), lampstate)

        
    def setLightOn(self, id):
        self.PUT('/lights/{0}/state'.format(id), '{"on": true}')
      
    def setLightOff(self, id):
        self.PUT('/lights/{0}/state'.format(id), {"on": False})
      

      
    def CLIP(self, method, resource, body, addUsername=True):

        reply = ""

        if type(body) == dict:
            body = json.dumps(body)

        url = '/api'    
        if addUsername == True:
            url += '/{0}'.format(self.username)
        url += resource

        if self.logfunc:
            self.logfunc('> {0}, {1}, {2}\n'.format(method, url, body))

        try:
            conn = httplib.HTTPConnection(self.ip)
            conn.request(method, url, body)
            resp = conn.getresponse()
            data = resp.read()

            reply = json.loads(data)
            conn.close()
        except Exception as e:
            if self.logfunc:
                self.logfunc('E {0}\n'.format(traceback.format_exc()))
            raise e
        else:
            if self.logfunc:
                self.logfunc('< {0}\n'.format(data))
        
        return reply
        

    def GET(self, resource):
        return self.CLIP("GET", resource, "")

        
    def PUT(self, resource, body):
        return self.CLIP("PUT", resource, body)

        
    def POST(self, resource, body, addUsername=True):
        return self.CLIP("POST", resource, body, addUsername)

        
    def DELETE(self, resource):
        return self.CLIP("DELETE", resource, "")
        
  
 

    