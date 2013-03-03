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


bridge_ip = "192.168.178.28"

CONTROLLING_LAMPS = 2


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
        print(ipstart)
        for i in range(1,254):
            #ip = "192.168.178.{0}".format(i)
            print(ipstart,i)
            self.q.put("{0}.{1}".format(ipstart, i))
        
    def FindBridges(self, progress=None, iprange=None):
        '''Crude first implementation, just try all addresses in the subnet'''
        self.bridges = []
        
        for i in range(50):
            t = Thread(target=self.FindBridgeTask)
            t.daemon = True
            t.start()

        rangecount = 0

        if (iprange is None):
            for ipaddress in [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.0.0.")]: # magic from the internet (works on my windows, not on OpenElec)
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
        for i in range(50):
            self.q.put("STOP")
        
        return self.bridges    


    def GetBridgeFromIp(self, ip):
        print(ip)
        bridge = 0
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
                
        
    def FindBridgeById(self, bridgeid):
        pass


class Bridge:
    '''Represents the bridge, use it to control the lights'''
    ip = 0
    id = 0
    name = "Default name"
    authorized = False
    
    authorizeThread = None
    authorizeDuration = 0;
    authorizeDeviceType = "Nothing"
    authorizeUser = "DefaultUser"
    
    def __init__(self, ip, id, name):
        self.ip = ip
        self.id = id
        self.name = name

    def __repr__(self):
        return "{0} - {1} - {2}".format(self.name, self.id, self.ip)
        

    def authorize(self, devicetype, username):
        # Attempt to create a user
        self.authorizeDeviceType = devicetype
        self.authorizeUser = username

        data = {'username':self.authorizeUser, 'devicetype':self.authorizeDeviceType}
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
        
    def isAuthorized(self, user):
        # Just get teh config and check for something in there
        conn = httplib.HTTPConnection(self.ip)
        conn.request("GET", '/api/{0}/config'.format(user), "") 
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
        conn.request("GET", '/api/{0}'.format(user), "") 
        resp = conn.getresponse()
        data = resp.read()
        #print data
        reply = json.loads(data)
        conn.close()  
#        print data
#        print(reply)
        
        return reply
        
    def sendLightState(self, id, json):
        conn = httplib.HTTPConnection(self.ip)
        conn.request("PUT", '/api/{0}/lights/{1}/state'.format(self.authorizeUser, id), json) 
        resp = conn.getresponse()  # Ignore response for now, assume it all went OK
        data = resp.read()
        print data
        conn.close()

    def sendGroupAction(self, id, json):
        conn = httplib.HTTPConnection(self.ip)
        conn.request("PUT", '/api/{0}/groups/{1}/action'.format(self.authorizeUser, id), json) 
        print('/api/{0}/groups/{1}/action'.format(self.authorizeUser, id))
        resp = conn.getresponse()  # Ignore response for now, assume it all went OK
        data = resp.read()
        print data
        conn.close()
        
    def setLightOn(self, id):
        self.sendLightState(self, id, '{"on": true}')
      
    def setLightOff(self, id):
        self.sendLightState(id, '{"on": false}')
      
    def setLightBri(self, id, bri):
        data = {'bri':int(bri), 'transitiontime': 20 }
        self.sendLightState(id, json.dumps(data))
        
    def setGroupAlert(self, id):
        data = {'alert':'select'}
        self.sendGroupAction(id, json.dumps(data))

    
  
 

    