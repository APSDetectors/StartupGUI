#!/local/anaconda2/bin/python2.7
#######!/APSshare/anaconda/x86_64/bin/python

#######!/APSshare/epd/rh6-x86/bin/python2.7
#######!/APSshare/anaconda/x86_64/bin/python2.7
#
#  wx_rocketLauncher
#  
#  This is a wxPython GUI is designed to be the 
#  master launch window for all supported detectors.
#
#  Authors: Russell Woods, Matthew Moore, Christopher Piatak
#		Date: 05/20/2013
#		      08/16/2013
#		      11/25/2013
#		      04/23/2014 ----> Fixing crashing for lack of wxCallAfter and added Mythen
#		      05/05/2014 ----> Updates to Mar345, Prosilica and Mar165
#		      06/02/2014 ----> Add Andor Neo and Pixirad
#		      09/11/2014 ----> updating Mythen
#		      12/09/2014 ----> updates for changes in how we start MEDMs/ImageJ
#		      12/18/2014 ----> Fixing so that you can't open more than one copy of a window 
#		      01/20/2015 ----> Update to Pilatus
#		      02/20/2015 ----> Added Merlin
#		      03/25/2015 ----> Updated Prosilica, Pixirad, Neo, Mar345, Mar165
#		      04/28/2015 ----> add REFRESH CONFIG files to the enu bar, fix verison control and naming standards
#         07/15/2015 ----> Updated Mythen
#         08/20/2015 ----> Added Xspress3
#         03/24/2016 ----> Added Ikon

import wx
import commands
import os
import signal
import subprocess

from threading import Thread 

import sys

#import DetectorList
import wx_splashScreen
import time

# Import xraydetector dependent info
sys.path.append("/local/config/")
import xrd_config

# Constants
WINDOW_WIDTH = 340
WINDOW_HEIGHT = 131


class StartFrame(wx.Frame):
	'''The Master Window'''

	# Globals:
	DETECTOR_CHOICE = "Detector"

	def __init__(self):
		wx.Frame.__init__(self, wx.GetApp().TopWindow, title = 'DP EPICS Launcher - Master', pos=(100, 200), size=(WINDOW_WIDTH, WINDOW_HEIGHT))

		# Make the panel
		self.background = wx.Panel(self)
		self.DPWindows=dict()

		# Make a Menu Bar
		self.menubar = wx.MenuBar()

		# Make a Menu
		self.helpDocs = wx.Menu()
		self.helpDocs.Append(101, '&Prosilica', '') 
		self.helpDocs.Append(102, '&Vortex',    '')
		self.helpDocs.Append(103, '&Mar345',    '')
		self.helpDocs.Append(104, '&Mar165',    '')
		self.helpDocs.Append(105, '&Pilatus',    '')
                self.helpDocs.Append(106, '&Cryostream',    '')
                self.helpDocs.Append(107, '&Pixirad-1',    '')
		wx.EVT_MENU(self, 101, self.helpDocs_101_Event)
		wx.EVT_MENU(self, 102, self.helpDocs_102_Event)
		wx.EVT_MENU(self, 103, self.helpDocs_103_Event)
		wx.EVT_MENU(self, 104, self.helpDocs_104_Event)
		wx.EVT_MENU(self, 105, self.helpDocs_105_Event)
                wx.EVT_MENU(self, 106, self.helpDocs_106_Event)
                wx.EVT_MENU(self, 107, self.helpDocs_107_Event)

		# Make a SubMenu
		#self.submenu_Linkam = wx.Menu()
		#self.submenu_Linkam = wx.Menu()
		#self.submenu_Linkam.Append(301, '&TS1500',  '')
		#self.submenu_Linkam.Append(302, '&THMS600', '')
		#self.submenu_Linkam.Append(303, '&DSC600',  '')
		#wx.EVT_MENU(self, 301, self.helpDocs_301_Event)
		#wx.EVT_MENU(self, 302, self.helpDocs_302_Event)
		#wx.EVT_MENU(self, 303, self.helpDocs_303_Event)
		#self.helpDocs.AppendMenu(104, '&Linkam', self.submenu_Linkam)
		self.menubar.Append(self.helpDocs, '&Help Documents')
		
		# DP Info Menu
		self.DPInfoMenu = wx.Menu()
		self.DPInfoMenu.Append(201, '&Pager', '')
		self.DPInfoMenu.Append(204, '&Equipment Requests', '')
		self.DPInfoMenu.Append(202, '&General', '')
		self.DPInfoMenu.Append(203, '&Detector Group', '')
                self.DPInfoMenu.Append(205, '&Version List', '')
		wx.EVT_MENU(self, 201, self.Pager_Event)
		wx.EVT_MENU(self, 202, self.DPGeneral_Event)
		wx.EVT_MENU(self, 203, self.DetectorGroup_Event)
		wx.EVT_MENU(self, 204, self.Requests_Event)
                wx.EVT_MENU(self, 205, self.VersionList_Event)
		self.menubar.Append(self.DPInfoMenu, '&Detector Pool')
		
		# Refresh Save Files Menu
		self.SaveMenu = wx.Menu()
		self.SaveMenu.Append(401, '&Connect to Archive...', '')
		self.SaveMenu.Append(402, '&Help', '')
		wx.EVT_MENU(self, 401, self.Connect_Event)
		wx.EVT_MENU(self, 402, self.Help_Event)
		self.menubar.Append(self.SaveMenu, '&Refresh Configs')
		
		self.SetMenuBar(self.menubar)
		
		# Make a Banner Title
		self.title = wx.StaticText(self.background, label="Select Detector")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))

		# Make Detector ComboBox
		self.detectorBox = wx.ComboBox(self.background, -1, self.DETECTOR_CHOICE, size=(250,25), choices=xrd_config.DETECTOR_LIST, style=wx.CB_READONLY)

		# Launch Button
		self.load = wx.Button(self.background, -1, 'Load')
		self.load.Bind(wx.EVT_BUTTON, self.load_Event)

		# Make a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Organization		
		self.horizontalBox_1 = wx.BoxSizer(wx.HORIZONTAL)
		self.horizontalBox_1.Add(self.detectorBox, proportion=1, border=0)
		self.horizontalBox_1.Add(self.load, proportion=0, border=5)

		self.verticalBox_1 = wx.BoxSizer(wx.VERTICAL)
		self.verticalBox_1.Add(self.title)
		self.verticalBox_1.Add(self.horizontalBox_1, proportion=1)
		self.background.SetSizer(self.verticalBox_1)
		self.background.Fit()
		#self.Fit()
		self.Center()
		
		self.Show()
	
	
	# These Methods handle HelpDoc Menu items
	def Connect_Event(self, event):
		tempCommand = ['/local/DPbin/Scripts/saveRestore_archive_REMOTE.linux']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
	
	def Help_Event(self, event):
		pgrDLG = wx.MessageDialog(self,"This tool connects to the Detector Pool archive to exchange the newest verisons of '.sav' and '.cfg' files.", "Help", wx.OK|wx.ICON_INFORMATION)
		pgrDLG.ShowModal()
		pgrDLG.Destroy()
	
	def helpDocs_101_Event(self, event):
		tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Scintillator-and-Visible-Light-Detectors#Prosilica']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_102_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Spectroscopic-Detectors#Vortex']
		#tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Vortex_SDD_SII_Nano']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_103_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Area-Detectors#Mar345']
		#tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Mar_345_Image_Plate/index.html']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_104_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Area-Detectors#Mar165CCD']
		#tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Mar_165_CCD_Camera/index.html']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_105_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Area-Detectors#Pilatus']
		#tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/PilatusII_100K/']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

        def helpDocs_106_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Sample-Environment#CryoStream']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

        def helpDocs_107_Event(self, event):
                tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Area-Detectors#pixirad']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)


	def helpDocs_301_Event(self, event):
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Equipment_Information/Linkam_TS1500/']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_302_Event(self, event):
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Equipment_Information/Linkam_THMS600/']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def helpDocs_303_Event(self, event):
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Equipment_Information/Linkam_Optical_DSC/']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def Pager_Event(self, event):
		pgrDLG = wx.MessageDialog(self,"The Detector Pool has someone on call 24 hours a day during the APS run to support users of Detector Pool equipment and other general issues. To get in touch with the Detector Pool call 2-9490 from any Argonne phone. The Detector Pool staff can also be contacted by e-mailing dp@aps.anl.gov.", "Detector Pool 2-9490", wx.OK|wx.ICON_INFORMATION)
		pgrDLG.ShowModal()
		pgrDLG.Destroy()
		
	def DPGeneral_Event(self, event):
		pgrDLG = wx.MessageDialog(self,"The Detector Pool has a number of differnt detectors and equipment availible for user to borrow. We try to make sure that we have the most up to dat equipment availble to user. To aid in this, please acknowledge the APS Detector Pool in any papers that make use of our equipment. This will allow us to show our scientific impact and ensure that everyone at APS can have acces to the latest and greatest detector in the world. \n\nInformation about the detector that are currently availble can be found at: http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/", "Detector Pool Info", wx.OK|wx.ICON_INFORMATION)
		pgrDLG.ShowModal()
		pgrDLG.Destroy()
		
	def DetectorGroup_Event(self, event):
		pgrDLG = wx.MessageDialog(self,"More information availible at http://www.aps.anl.gov/Xray_Science_Division/Detectors/", "Detector Group Infomation", wx.OK|wx.ICON_INFORMATION)
		pgrDLG.ShowModal()
		pgrDLG.Destroy()
		
	def Requests_Event(self, event):
		tempCommand = ['firefox', 'https://beam.aps.anl.gov/pls/apsweb/wam0002.dds_main_menu']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
         
        def VersionList_Event(self, event):
                tempCommand = ['cd /local/DPbin/build_testing;./epics_module_version_list.py /local/DPbin/epics/epics_2020-03-17; cd /local/DPbin/epics/epics_2020-03-17; nedit module_version_list.txt']
                #tempCommand = ['cd /local/DPbin/epics/epics_2020-03-17; less module_version_list.txt; cd /local/DPbin/build_testing;./epics_module_version_list.py; /local/DPbin/epics/epics_2020-03-17']
                #tempCommand = ['cd /local/DPbin/Scripts; ./start_epics_version_list']
		p_ioc = subprocess.Popen(tempCommand, shell=True, preexec_fn=os.setsid) 


        #def VersionList_Event(self, event):
                #tempCommand = ['cd /local/DPbin/epics/epics_2020-03-17;libreoffice module_version_list.txt']
		#p_ioc = subprocess.Popen(tempCommand, shell=True, preexec_fn=os.setsid)
                ##pgrDLG = wx.MessageDialog(self, " ", "Version_list_2020", wx.OK|wx.ICON_INFORMATION)
                ##pgrDLG.ShowModal()
                ##pgrDLG.Destroy()                             
   
        #def VersionList_Event(self, event):
                #pgrDLG = wx.MessageDialog(self, "DET", "Version_list_2020", wx.OK|wx.ICON_INFORMATION)
		#pgrDLG.ShowModal()
		#pgrDLG.Destroy()
                


	# This Method launches the Detector Windows
	def load_Event(self, event):
		print "\nLoading " + str(self.detectorBox.GetValue()) + "..."

		if(self.detectorBox.GetValue() == 'Vortex'):
			import wxVortex										# wx.CallAfter fixed
			try:
				self.DPWindows['vortex'] != None	
			except:
				self.DPWindows['vortex'] = wxVortex.VortexFrame(parent=self)
			
			self.DPWindows['vortex'].Center()
			self.DPWindows['vortex'].Show()
			self.DPWindows['vortex'].SetFocus()

		elif(self.detectorBox.GetValue() == 'Prosilica'):
			import wxProsilica									# wx.CallAfter fixed
			try:
				self.DPWindows['prosilica'] !=None
			except:
				self.DPWindows['prosilica'] = wxProsilica.ProsilicaFrame(parent=self)
			
			self.DPWindows['prosilica'].Center()
			self.DPWindows['prosilica'].Show()

		elif(self.detectorBox.GetValue() == 'Linkam'):
			import wxLinkam										# wx.CallAfter fixed
			try:
				self.DPWindows['linkam']!=None
			except:
				self.DPWindows['linkam'] = wxLinkam.LinkamFrame(parent=self)
				
			self.DPWindows['linkam'].Center()
			self.DPWindows['linkam'].Show()

		elif(self.detectorBox.GetValue() == 'Mar345'):
			import wxMar345										# wx.CallAfter fixed
			try:
				self.DPWindows['mar345'] !=None
			except:
				self.DPWindows['mar345'] = wxMar345.Mar345Frame(parent=self)
				
			self.DPWindows['mar345'].Center()
			self.DPWindows['mar345'].Show()

		elif(self.detectorBox.GetValue() == 'Mar165'):
			import wxMar165										# wx.CallAfter fixed
			try:
				self.DPWindows['mar165']!=None
			except:
				self.DPWindows['mar165'] = wxMar165.Mar165Frame(parent=self)
			self.DPWindows['mar165'].Center()
			self.DPWindows['mar165'].Show()

		elif(self.detectorBox.GetValue() == 'Pilatus'):
			import wxPilatus
			try:
				self.DPWindows['pilatus']!=None
			except:
				self.DPWindows['pilatus'] = wxPilatus.PilatusFrame(parent=self)
				
			self.DPWindows['pilatus'].Center()
			self.DPWindows['pilatus'].Show()
			
		elif(self.detectorBox.GetValue() == 'CoolSnap'):
			import wxCoolSnap
			try:
				self.DPWindows['coolsnap']!=None
			except:
				self.DPWindows['coolsnap'] = wxCoolSnap.CoolSnapFrame(parent=self)
			self.DPWindows['coolsnap'].Center()
			self.DPWindows['coolsnap'].Show()
			
		elif(self.detectorBox.GetValue() == 'Mythen'):
			import wxMythen
			try:
				self.DPWindows['mythen']!=None
			except:
				self.DPWindows['mythen'] = wxMythen.MythenFrame(parent=self)
			self.DPWindows['mythen'].Center()
			self.DPWindows['mythen'].Show()
			
		elif(self.detectorBox.GetValue() == 'Andor'):
			import wxNeo
			try:
				self.DPWindows['andor']!=None
			except:
				self.DPWindows['andor'] = wxNeo.NeoFrame(parent=self)
			self.DPWindows['andor'].Center()
			self.DPWindows['andor'].Show()
			
		elif(self.detectorBox.GetValue() == 'Pixirad'):
			import wxPixirad
			try:
				self.DPWindows['pixirad']!=None
			except:
				self.DPWindows['pixirad'] = wxPixirad.PixiradFrame(parent=self)
			self.DPWindows['pixirad'].Center()
			self.DPWindows['pixirad'].Show()	
		elif(self.detectorBox.GetValue() == 'Merlin'):
			import wxMerlin as wxMerlinStart
			try:
				self.DPWindows['merlin']!=None
			except:
				self.DPWindows['merlin'] = wxMerlinStart.MerlinFrame(parent=self)
			self.DPWindows['merlin'].Center()
			self.DPWindows['merlin'].Show()
		elif(self.detectorBox.GetValue() == 'Xspress3'):
			import wxXspress3 as wxXspress3Start
			try:
				self.DPWindows['xspress3']!=None
			except:
				self.DPWindows['xspress3'] = wxXspress3Start.Xspress3Frame(parent=self)
			self.DPWindows['xspress3'].Center()
			self.DPWindows['xspress3'].Show()
			
		elif(self.detectorBox.GetValue() == 'Ikon'):
			import wxIkon
			try:
				self.DPWindows['ikon']!=None
			except:
				self.DPWindows['ikon'] = wxIkon.IkonFrame(parent=self)
			self.DPWindows['ikon'].Center()
			self.DPWindows['ikon'].Show()	
			
### Canberra #######	
	
		elif(self.detectorBox.GetValue() == 'Canberra'):
			import wxCanberra									# wx.CallAfter fixed
			try:
				self.DPWindows['Canberra'] !=None
			except:
				self.DPWindows['Canberra'] = wxCanberra.CanberraFrame(parent=self)
			
			self.DPWindows['Canberra'].Center()
			self.DPWindows['Canberra'].Show()
### PointGrey ######
		elif(self.detectorBox.GetValue() == 'PointGrey'):
			import wxPointGrey
			try:
				self.DPWindows['pointGrey']!=None
			except:
				self.DPWindows['pointGrey'] = wxPointGrey.PointGreyFrame(parent=self)
				
			self.DPWindows['pointGrey'].Center()
			self.DPWindows['pointGrey'].Show()
### Cryostat ######
	        elif(self.detectorBox.GetValue() == 'Cryostat'):
			import wxCryostat
			try:
				self.DPWindows['Cryostat']!=None
			except:
				self.DPWindows['Cryostat'] = wxCryostat.CryostatFrame(parent=self)
				
			self.DPWindows['Cryostat'].Center()
			self.DPWindows['Cryostat'].Show()

###Added Eiger 02/20/2020####
                elif(self.detectorBox.GetValue() == 'Eiger'):
                        import wxEiger
                        try:
                                self.DPWindows['eiger']!=None
                        except:
                                self.DPWindows['eiger'] = wxEiger.EigerFrame(parent=self)
                        self.DPWindows['eiger'].Center()
                        self.DPWindows['eiger'].Show()
####################	
			
		else: print "Detector not supported yet..."

	# This method Prompts the User for confimation when closing the Window
	def OnClose(self, event):
		dlg = wx.MessageDialog(self,"Do you really want to close DP EPICS Launcher?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_OK:
			for w in self.DPWindows.keys():
				try:
					self.DPWindows[w].Close()
				except:
					print "\n"
			self.Destroy()

'''	
	def PollThread(self, event):
		if self.testThread.isAlive():
			print "it's alive!"	
'''



#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

class MyApp(wx.App):
	def OnInit(self):
		
		# Make instance of main GUI class
		frame = StartFrame()
		frame.Show()
		return True


app = MyApp(0)
# Splash
splash = wx_splashScreen.DPSplashScreen()

app.MainLoop()





