#
# Code for testing stuff in the hue.py file
#

import hue
import huecontrol
import time


BRIDGEID = "00178809a0e5"
BRIDGEIP = "192.168.178.28"

bridge = hue.BridgeLocator().FindBridgeById(BRIDGEID)

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge


bridge = hue.BridgeLocator().FindBridgeById(BRIDGEID, "1.2.3.4")

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge


bridge = hue.BridgeLocator().FindBridgeById(BRIDGEID, BRIDGEIP)

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge


bridge = hue.BridgeLocator().GetBridgeFromIp(BRIDGEIP)
bridge.username = huecontrol.BRIDGEUSER
bridge.devicetype = huecontrol.DEVICETYPE

print bridge

#for bridge in bridges:
print bridge.isAuthorized()

# Expect 101 error because the button is not pressed
result = bridge.authorize()
print result
if result != 101:
    print "Unexpected result " + result

#bridge.setGroupAlert(0)

bridge.setGroupBri(0, 250)

fullstate = bridge.getFullState()
print str(fullstate)[:250]

# Dim lights and restore light 1 and 3
bridge.setGroupBri(0, 100)
bridge.setFullStateLights(fullstate, [1,3])

# Wait till restored
time.sleep(2)

# Dim lights and restore all
bridge.setGroupBri(0, 100)
bridge.setFullStateLights(fullstate)






