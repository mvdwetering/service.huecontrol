#
# Code for testing stuff in the hue.py file
#

import hue
import time
import huecontrol


BRIDGEID = "00178809a0e5"
BRIDGEIP = "192.168.178.140"

# To skip the searching tests as they take long
skipSearching = False

if not skipSearching:
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


bridge = hue.BridgeLocator(BRIDGEIP).GetBridgeFromIp(BRIDGEIP)

if not bridge:
    print "ERROR: Bridge not found"
else:
    print "Found bridge: "
    print bridge

    
def log(message):
    print message
    
bridge.username = huecontrol.BRIDGEUSER
bridge.devicetype = huecontrol.DEVICETYPE
bridge.logfunc = log


#for bridge in bridges:
print bridge.isAuthorized()

# Expect 101 error because the button is not pressed
result = bridge.authorize()
print result
if result != 101:
    print "Unexpected result " + str(result)


fullstate = bridge.getFullState()
print "First 250 chars of state:\n" + str(fullstate)[:250]

# Dim lights and restore light 1 and 3
bridge.PUT('/groups/0/action', {'bri':100})
bridge.setFullStateLights(fullstate, [1,3])

# Wait till restored
time.sleep(2)

# Now some without log function
bridge.logfunc = None


# Dim lights and restore all
bridge.PUT('/groups/0/action', {'bri':100})
bridge.setFullStateLights(fullstate)






