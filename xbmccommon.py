#
# Common code for xbmc related stuff
#

import xbmc, xbmcaddon
import os


ADDON_ID = 'service.huecontrol'


__addon__ = xbmcaddon.Addon(id=ADDON_ID)
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")  # Translate path to change special:// protocol to a normal path
__addonicon__ = os.path.join(__addonpath__, 'icon.png')
__language__ = __addon__.getLocalizedString


# Just a wrapper to keep icons and title easier consistent
def notify(text, duration=3000, title=None):
    if title == None:
        title = __language__(30000)
    
    xbmc.executebuiltin('Notification("{1}","{2}", {3}, {0})'.format(__addonicon__, title, text, duration))
