# file : wx_splashScreen.py


#	This is a wxPython GUI Class for the
#	Detector Pool splash screen 
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 8/23/2013


import wx


class DPSplashScreen(wx.SplashScreen):
    """
	Create a splash screen widget.
    """
    def __init__(self, parent=None):

        # This is a recipe to a the screen.
        splashBitmap = wx.Image(name = "/local/DPbin/wxDPStartup/DP-EPICS-Startup-Screen.jpg").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 2000  # milliseconds

        # Call the constructor with the above arguments in exactly the following order.
        wx.SplashScreen.__init__(self, splashBitmap, splashStyle, splashDuration, parent)
        wx.Yield()
        
        
