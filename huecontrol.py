#
# Hue controller common defines
#

import xbmc, xbmcaddon
import os
import errno


ADDON_ID = 'service.huecontrol'

BRIDGEUSER = "65c3f3f7caf6f3c782a5cf3ed8b25de2c83e5b07"
DEVICETYPE = "XBMC hue control"

MAX_LAMPS = 15



__addon__ = xbmcaddon.Addon(id=ADDON_ID)
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonicon__ = os.path.join(__addonpath__, 'icon.png')
__language__ = __addon__.getLocalizedString


# Just a wrapper to keep icons and title easier consistent
def notify(text, duration=3000, title=None):
    if title == None:
        title = __language__(30000)
    
    xbmc.executebuiltin('Notification("{1}","{2}", {3}, {0})'.format(__addonicon__, title, text, duration))
