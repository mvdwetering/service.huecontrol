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
import requests

MAX_LAMPS = 63   # Max lamps supported by the bridge
NUM_THREADS = 20 # Number of threads spawned when searching the network for bridges

class BridgeLocator:
    '''Class that finds hue bridges in the network'''
    bridges = []
    lock = Lock()
    q = Queue()

    def __init__(self, iprange=None, logfunc=None):
        self.iprange = iprange
        self.logfunc = logfunc
        
        self.log("BridgeLocator iprange:{0}".format(iprange))

    def FindBridgeTask(self):
        done = False
        while not done:
            item = self.q.get()
            self.log("Check IP: {0}".format(item))

            sys.stdout.write('.')
            if item == "STOP":
                done = True
            else:
                bridge = self.GetBridgeFromIp(item)
                if bridge:
                    with self.lock:
                        #self.bridges.append(bridge)
                        self.bridgesById[bridge.id] = bridge;

            self.q.task_done()

    def SearchIpRange(self, iprange=None):
    
        if iprange == None:
            iprange = self.iprange;

        self.log("SearchIpRange {0}".format(iprange))

        tmp = iprange.rfind('.')
        ipstart = iprange[0:tmp]
        for i in range(1,254):
            self.log("Adding IP address {0}.{1}".format(ipstart,i))
            self.q.put("{0}.{1}".format(ipstart, i))
        
    def FindBridges(self, progress=None):
        '''Crude first implementation, just try all addresses in the subnet'''
        #self.bridges = []
        self.bridgesById = {}

        # First try nupnp
        r = requests.get('http://www.meethue.com/api/nupnp', timeout=2)
        if r.status_code == 200:
            bridgelist = r.json()
            
            for nupnp_bridge in bridgelist:
                self.log(str(nupnp_bridge))
                
                # Ignore the ID, that will be fetched from the bridge if it exists at the given IP address
                bridge = self.GetBridgeFromIp(nupnp_bridge["internalipaddress"])
                if bridge:
                    #self.bridges.append(bridge);
                    self.bridgesById[bridge.id] = bridge;
        

        # Now start scan on local network
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
                time.sleep(0.3)
        
            progress(100)    # Done ;-)

        self.q.join()
        
        # Done with the threads, time to close them down, otherwise they hang Kodi when tying to close it
        for i in range(NUM_THREADS):
            self.q.put("STOP")

        # Convert to a list
        bridges = []
        for bridgeid in self.bridgesById.keys():
            bridges.append(self.bridgesById[bridgeid]);
        
        return bridges    


    def GetBridgeFromIp(self, ip):
        self.log("GetBridgeFromIp {0}".format(ip))

        bridge = None
        try:
            conn = httplib.HTTPConnection(ip, timeout=1)
            conn.request("GET", '/api/nouser/config') 
            resp = conn.getresponse()
            data = resp.read()

            self.log("{0}, {1}, {2}".format(ip, resp.status, data))
            
            if (resp.status == 200):
                # Got a config back. Parse it to get the bridge ID (and name)
                config = json.loads(data)
                
                # Older versions of the addon used the "serial" found in the description.xml this seems to be the macaddress without the colons.
                # The new software with API 1.10 and up have a "bridgeid" in /config, this seems to be the macaddress with "fffe" stuffed in the middle, use that if available (and use the lowercase as on the /nupnp)
                # If not available use the "mac" attribute in config to be able to work with older bridge software versions
                bridgeid = None
                if "bridgeid" in config:
                    bridgeid = config["bridgeid"].lower()
                elif "mac" in config:
                    self.log("Found a bridge with very old software version({0}) at IP {1}. You might want to update the bridge software with the Philips Hue app.".format(config["swversion"], ip))
                    mac = config["mac"].translate(None, " :")
                    bridgeid = "{0}fffe{1}".format(mac[0:6], mac[6:12]).lower()
                else:
                    self.log("Unable to detect bridge ID! Try updating the bridge software with the Philips Hue app")
                
                # An old (round) bridge can have been migrated to a new (square) bridge.
                # store the replacesbridgeid to ba able to detect migrated bridges for seamless transition
                replacesbridgeid = None
                if "replacesbridgeid" in config and config["replacesbridgeid"] != None:
                    replacesbridgeid = config["replacesbridgeid"].lower()

                friendlyname = config["name"]
                
                bridge = Bridge(ip, bridgeid, friendlyname, replacesbridgeid=replacesbridgeid)

            conn.close()
            
        except Exception as e:
            self.log("{0} Could not connect to {1}\n{2}".format(str(datetime.now()), ip, e))
            #self.log(traceback.print_exc())
            pass
    
        return bridge
                
        
    def FindBridgeById(self, bridgeid, lastip=None):
       
        # Try last known IP if provided
        if lastip:
            bridge = self.GetBridgeFromIp(lastip)
            if bridge and bridge.id == bridgeid:
                return bridge;
                
        # Not found at last IP just find all and filter.
        bridges = self.FindBridges()

        # First try to find an exact match
        for bridge in bridges:
            if bridge.id == bridgeid:
                return bridge;

        # See if there is a bridge that was migrated from the desired ID
        for bridge in bridges:
            if bridge.replacesbridgeid == bridgeid:
                # TODO update the stored bridge ID?
                return bridge;
        
        return None

    def log(self, msg):
        if self.logfunc:
            self.logfunc(msg)
        

class Bridge:
    '''Represents the bridge, use it to control the lights'''
    ip = 0
    id = 0
    name = "Philips hue"
    username = None
    devicetype = None
    authorized = False
    

    def __init__(self, ip=None, id=None, name=None, devicetype=None, username=None, logfunc=None, replacesbridgeid=None):
        self.ip = ip
        self.id = id
        self.name = name
        self.devicetype = devicetype
        self.username = username
        self.logfunc = logfunc
        self.replacesbridgeid = replacesbridgeid

    def __repr__(self):
        return "{0} - {1} - {2}".format(self.name, self.id, self.ip)
        

    def authorize(self):
        # Attempt to create a user
        data = {'devicetype': self.devicetype}
        
        #jsonstr = json.dumps(data)
        reply = self.POST("", data, addUsername=False)
        
        if ('success' in reply[0]):
            self.username = reply[0]["success"]["username"]  # Will be random name
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

        return reply; # json.dumps(reply)  # return the string so the receiver can easily store it (relevant for saving settings in Kodi which must be strings)
        
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

        for i in range(1, MAX_LAMPS+1):
            strId = str(i)
            
            if  not lightList or (i in lightList):

                if (strId in lights):
                    storedstate = lights[strId]['state']
                    self.log("setFullStateLights ID:{0}, State:{1}".format(strId, storedstate))

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

        self.log('> {0}, {1}, {2}\n'.format(method, url, body))

        try:
            r = requests.request(method, "http://{0}{1}".format(self.ip, url), data=body, timeout=1.5)
            reply = r.json()
        except requests.exceptions.ConnectTimeout as e:
            self.log("Connection timeout! IP:{0}, URL:{1}".format(self.ip, url))
        except Exception as e:
            self.log('E {0}\n'.format(traceback.format_exc()))
            raise e
        else:
            self.log('< {0}\n'.format(reply))
        
        return reply
        

    def GET(self, resource):
        return self.CLIP("GET", resource, "")

        
    def PUT(self, resource, body):
        return self.CLIP("PUT", resource, body)

        
    def POST(self, resource, body, addUsername=True):
        return self.CLIP("POST", resource, body, addUsername)

        
    def DELETE(self, resource):
        return self.CLIP("DELETE", resource, "")
        
    def log(self, msg):
        if self.logfunc:
            self.logfunc(msg)
 

    