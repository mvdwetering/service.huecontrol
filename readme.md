Hue Control
===========

About
-----
Hue Control is a Kodi addon that can change your hue lights when starting a movie.
Next to that it has a few preset slots that you can use to recall any lightsetting you created earlier with your TV remote.


Installation
------------
Just install from the zip file
When updating the addon make sure to disable and enable the addon listed under Services/huecontrol because Kodi does not restart it automatically (Restarting Kodi also works).

If you have problems upgrading the addon then:
- Uninstall the addon
- Restart Kodi
- Install the addon


Setup
-----
In the addons settings screen you will fist have to connect to your bridge. Follow the instructions from the addon to go through the procedure.

You can select which lamps to control in the settings window (e.g. only the lamps in the livingroom). By default 3 lamps are selected.

By default the following behaviours are configured:
- When playing a movie the lights will go out
- When pausing a movie the lights will go to a low brightness setting
- When stopping a movie the lights return to their original state.

If you want to change the settings of the lamps go to the "Presets" section in the settings.

1. Locate the preset you want to change. 
The "Playing" and "Paused" presets will be automatically selected when playing/pausing a movie. The other presets are available in the presets menu that can be opened when opening the addon from te programs section of Kodi or you can bind it to a key on your remote control through the keymap.xml by adding the following for a key:
> RunScript(service.huecontrol,action=showpresets)

2. Set the lamps to the desired settings with an app (e.g. the Philips hue app)

3. Press the 'save lamp state' button for the preset under which you want to store the configuration. 


