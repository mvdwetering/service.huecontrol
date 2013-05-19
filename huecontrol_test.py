#
# Code for testing stuff in the hue.py file
#

import hue
import time


BRIDGEUSER = "65c3f3f7caf6f3c782a5cf3ed8b25de2c83e5b07"
DEVICETYPE = "XBMC hue control"

BRIDGEID = "00178809a0e5"
BRIDGEIP = "192.168.178.140"

bridge = hue.BridgeLocator().FindBridgeById(BRIDGEID)

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge


bridge = hue.BridgeLocator("1.2.3.4").FindBridgeById(BRIDGEID)

if not bridge:
    print "Bridge not found (as expected)"
else:
    print "ERROR: Found bridge: "
    print bridge


bridge = hue.BridgeLocator(BRIDGEIP).FindBridgeById(BRIDGEID)

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge


bridge = hue.BridgeLocator().GetBridgeFromIp(BRIDGEIP)
bridge.username = BRIDGEUSER
bridge.devicetype = DEVICETYPE

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






