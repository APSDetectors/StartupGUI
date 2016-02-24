# StartupGUI
APS Detector Pool Startup GUI for EPICS

EPICS Laucher has been developed for the APS Detector Pool (https://www1.aps.anl.gov/detectors) 
in order to make EPICS software start-up easier.  On Detector Pool computers, the GUI will start 
automatically after login. Select a detector from  dropdown menu and load. Choose the correct 
model number, bit depth, etc. (if needed). Start IOC; Start MEDM; Start additional software 
as needed (e.g. ImageJ, IDL-MCA).  We are currently working on custom Autosave files storage.

The Startup GUI is built with wxpython (any other dependences?)

Need to add more information on how to use and general structure of the software.

Some issues:
 * Hardwired to use /APSshare/epd/rh6-x86/bin/python2.7
 * Need to figure out how to import DPOStools and xrd_config which is on /local/config
 


