#
# Code for testing stuff in the hue.py file
#

import hue
import time

#bridges = hue.BridgeLocator().FindBridges()
#print bridges


bridge = hue.BridgeLocator().GetBridgeFromIp("192.168.178.28")

#for bridge in bridges:
print bridge.isAuthorized()
print bridge.isAuthorized("piet")
print bridge.isAuthorized("aValidUser")

print bridge.authorize()
#bridge.setGroupAlert(0)


    