#!wxCoolSnap

#  This is a wxPython GUI to launch the
#  CoolSnap CCD camera.   
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 05/20/2013
#     		08/08/2013
#			04/29/2015 - Added Quick Start Guide


import wx
import commands
import sys
import os
import signal
import subprocess
import time
import threading
import DPOStools as DPOStools

# Import pyEpics for initializing camera in pvCam
sys.path.append("/APSshare/epd/rh6-x86/lib/python2.7/site-packages/")
import epics 

# Import xraydetector dependent info
sys.path.append("/local/config/")
import xrd_config

# Import DPbin dependent info
sys.path.append("/local/DPbin/")
import DPbin_config

pv_Prefix = xrd_config.DP_PV_SECTOR + 'coolsnap'+ xrd_config.DP_PV_SUFFIX
binary='pvCamApp'
detector = 'coolsnap'

# Declare constants in capitals and as global variables at the start of your code
# This makes it much easier to change them later, especially if they are used often.
# It also indicates they are values that won't change throughout the programme's execution.

WINDOW_WIDTH = 200
WINDOW_HEIGHT = 10

class CoolSnapFrame(wx.Frame):
	'''CoolSnap Window'''
	
	# Globals
	pid_ioc = -999
	pid_medm = -999
	pid_imagej = -999


	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP CoolSnap Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		
		#Set PS checking wait time
		self.checkCycle=1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&CoolSnap', '')				# Add entry
		self.Bind(wx.EVT_MENU, self.helpDocs_101_Event, id=101)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar

		#--------------------------------------------------------------------------------------
		# CoolSnap
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="CoolSnap")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Launch and Stop Buttons:
		# IOC
		self.ioc_title = wx.StaticText(self.background, label="IOC\t")
		self.ioc_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.start_ioc_Btn = wx.Button(self.background, label = 'Start', size=[60,25])
		self.start_ioc_Btn.Bind(wx.EVT_BUTTON, self.start_ioc_Event)
		self.stop_ioc_Btn = wx.Button(self.background, label = 'Stop', size=[60,25])
		self.stop_ioc_Btn.Bind(wx.EVT_BUTTON, self.stop_ioc_Event)

		# MEDM
		self.medm_title = wx.StaticText(self.background, label="MEDM\t")
		self.medm_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.start_medm_Btn = wx.Button(self.background, label = 'Start', size=[60,25])
		self.start_medm_Btn.Bind(wx.EVT_BUTTON, self.start_medm_Event)
		self.stop_medm_Btn = wx.Button(self.background, label = 'Stop', size=[60,25])
		self.stop_medm_Btn.Bind(wx.EVT_BUTTON, self.stop_medm_Event)

		# IMAGEJ
		self.imagej_title = wx.StaticText(self.background, label="ImageJ\t")
		self.imagej_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.start_imagej_Btn = wx.Button(self.background, label = 'Start', size=[60,25])
		self.start_imagej_Btn.Bind(wx.EVT_BUTTON, self.start_imagej_Event)
		self.stop_imagej_Btn = wx.Button(self.background, label = 'Stop', size=[60,25])
		self.stop_imagej_Btn.Bind(wx.EVT_BUTTON, self.stop_imagej_Event)


		# Make Horizontal Box Sizers
		self.horizontalBox_1 = wx.BoxSizer(wx.HORIZONTAL)
		self.horizontalBox_1.Add(self.ioc_title, proportion = 1, border = 2,flag=wx.ALIGN_CENTER)
		self.horizontalBox_1.Add(self.start_ioc_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		self.horizontalBox_1.Add(self.stop_ioc_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)

		self.horizontalBox_2 = wx.BoxSizer(wx.HORIZONTAL)
		self.horizontalBox_2.Add(self.medm_title, proportion = 1, border = 2,flag=wx.ALIGN_CENTER)
		self.horizontalBox_2.Add(self.start_medm_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		self.horizontalBox_2.Add(self.stop_medm_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)

		self.horizontalBox_3 = wx.BoxSizer(wx.HORIZONTAL)
		self.horizontalBox_3.Add(self.imagej_title, proportion = 1, border = 2,flag=wx.ALIGN_CENTER)
		self.horizontalBox_3.Add(self.start_imagej_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		self.horizontalBox_3.Add(self.stop_imagej_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)


		# Make a vertical sizer
		self.verticalBox = wx.BoxSizer(wx.VERTICAL)
		self.verticalBox.Add(self.title, proportion = 0, border = 1, flag=wx.ALIGN_CENTER)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)

		self.verticalBox.Add(self.horizontalBox_1, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)

		self.verticalBox.Add(self.horizontalBox_2, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)

		self.verticalBox.Add(self.horizontalBox_3, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
		
		# PS checking
		self.running=True
		self.PSthread = threading.Thread(target=self.pscheck)
		self.PSthread.start()
		
		# Set the panel size
		self.background.SetSizer(self.verticalBox)
		self.background.Fit()
		self.Fit()
		self.Show()



	#--------------------------------------------------------------------------------------
	# Define Event Methods (button actions)   
	#         NOTE: Executed scripts MUST have a shebang! definition in line #1
	#--------------------------------------------------------------------------------------
	def helpDocs_101_Event(self, event):
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Photometrics_Roper_Cool_Snap/index.html']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	# This method Prompts the User for confimation when closing the Window
	def OnClose(self, event):
		if self.closeprompt:
			dlg = wx.MessageDialog(self,"Do you really want to close this app?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			result = dlg.ShowModal()
			dlg.Destroy()
		else:
			result = wx.ID_OK
			
		if result == wx.ID_OK:
			
			#Cleans up PSthread
			self.running=False
			
			while (self.PSthread.isAlive()):
				time.sleep(self.checkCycle)
			
			self.Hide()
			

	def start_ioc_Event(self, event):
		
		# Put the terminal command into a tuple (start_ioc, detector)
		
		if not(self.processes['IOC']['running']):
			
			#Have the psthread wait
			startIOC=threading.Condition()
			startIOC.acquire()
			# Start the subprocess
			subprocess.Popen(['/local/DPbin/Scripts/start_ioc', detector],  preexec_fn=os.setsid)
			# Grab the subprocess I.D.
			self.processes['IOC']['pid'] = DPOStools.waitforprocess(binary)
			self.processes['IOC']['running']=True
		
			print "\nOpening IOC..."
		
			# Set the Button Colour
			self.ioc_alive() 
			startIOC.release()
			self.SetWindowStyleFlag(wx.STAY_ON_TOP)
			self.SetWindowStyle(not(wx.STAY_ON_TOP))
			
			# Initialize camera in pvCam IOC
			epics.caput((pv_Prefix + ':cam1:Initialize'),1)
			
		else:
			print "\nIOC already running!"

	def stop_ioc_Event(self, event):
		# Kill the IOC
		if(self.processes['IOC']['running']):
			#print str(self.processes['IOC']['pid'])
			os.kill(self.processes['IOC']['pid'], signal.SIGTERM)
			self.new_dead("IOC")
			print "\nIOC was stopped by user."
		else:
			print "\nNo process to stop."

	def start_medm_Event(self, event):
		# Put the terminal command into a tuple

		if not(self.processes['MEDM']['running']):
			
			#stop other threads
			startMEDM=threading.Condition()
			startMEDM.acquire()
			
			tempCommand = ['/local/DPbin/Scripts/start_medm_coolsnap', pv_Prefix]
			
			# Start the subprocess
			subprocess.Popen(tempCommand,  preexec_fn=os.setsid)
			# Grab the subprocess I.D.
			self.processes['MEDM']['pid'] = DPOStools.waitforprocess("medm -x -macro P="+pv_Prefix)
			self.processes['MEDM']['running']=True
			#print self.pid_medm
			print "\nOpening MEDM..."
			#print "Process i.d. = " + str(self.pid_medm)
			# Set the Button Colour
			self.medm_alive()
			startMEDM.release()
			
		else:
			print "\nMEDM already running!"

	def stop_medm_Event(self, event):
		# Kill the MEDM
		if(self.processes['MEDM']['running']):
			os.kill(self.processes['MEDM']['pid'], signal.SIGTERM)
			self.new_dead("MEDM")
			
			print "\nMEDM was stopped by user."
		else:
			print "\nNo process to stop."
			
			
	def start_imagej_Event(self, event):
		# Put the terminal command into a tuple
			
		
		# Start the subprocess	
		tempCommand = ['/local/DPbin/Scripts/start_imageJ', pv_Prefix]
		
		p_imagej = subprocess.Popen(tempCommand, preexec_fn=os.setsid)
		# Grab the subprocess I.D.
		self.pid_imagej = self.processes['ImageJ']['pid'] = DPOStools.waitforprocess("EPICS AD Viewer")
		print "\nOpen ImageJ..."
		#print "Process i.d. = " + str(self.pid_imagej)
		# Set the Button Colour
		self.new_alive(self.start_imagej_Btn)
			
			

	def stop_imagej_Event(self, event):
		# Kill the ImageJ
		if(self.processes['ImageJ']['running']):
			os.kill(self.processes['ImageJ']['pid'], signal.SIGKILL)
			self.new_dead('ImageJ')
			print "\nImageJ was stopped by user."
		else:
			print "\nNo process to stop."

	
		
	def new_dead(self, app):
		self.processes[app]={
								'pid':	-999,
								'running':False,
								}
		if app=="MEDM":
			button = self.start_medm_Btn
		elif app=="IOC":
			button = self.start_ioc_Btn
		elif app=="ImageJ":
			button= self.start_imagej_Btn
		else:
			print "ERROR, unknown app!"
				
		button.SetBackgroundColour(wx.WHITE)
		button.SetLabel("Start") 
		
	def ioc_alive(self):
		self.new_alive(self.start_ioc_Btn)

		
	def medm_alive(self):
		self.new_alive(self.start_medm_Btn) 
		
	def new_alive(self, button):
		button.SetBackgroundColour(wx.GREEN)
		button.SetLabel("Running")

	def pscheck(self):
		self.processes={
						'IOC':
								{
								'pid':	-999,
								'running':False,
								},
						'MEDM':
								{
								'pid':	-999,
								'running':False,
								},
						'ImageJ':
								{
								'pid':	-999,
								'running':False,
								},
						}
		
		while (self.running):
			#IOC check
			
			try:
				results=subprocess.check_output(["pgrep", "-f", binary])
				self.processes['IOC']['pid']=int(results)
				if not(self.processes['IOC']['running']):
					self.ioc_alive()
					self.processes['IOC']['running']=True
				
			except:
				if self.processes['IOC']['running']:
					self.new_dead("IOC")
			
					
			#MEDM check
			try:
				results=subprocess.check_output(["pgrep", "-f", "medm -x -macro P="+pv_Prefix])
				self.processes['MEDM']['pid']=int(results)
				#print "IOC Process: " + str(self.processes['MEDM']['pid'])
				#print self.processes['MEDM']['running']
				if not(self.processes['MEDM']['running']):
					self.medm_alive()
					self.processes['MEDM']['running']=True
				
			except:
				if self.processes['MEDM']['running']:
					self.new_dead("MEDM")
					
					
					
			#ImageJ
			try:
				results=subprocess.check_output(["pgrep", "-f", "EPICS AD Viewer"])
				self.processes['ImageJ']['pid']=int(results)
				if not(self.processes['ImageJ']['running']):
					self.new_alive(self.start_imagej_Btn)
					self.processes['ImageJ']['running']=True
				
			except:
				if self.processes['ImageJ']['running']:
					self.new_dead("ImageJ")
					
			time.sleep(self.checkCycle)

#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

# Make an application
#app_2 = wx.App(redirect=False)

# Make an instance of the class - the Topmost GUI element
#startTest = StartFrame()
#russTest = ProsilicaFrame()

# Let it run!
#app_2.MainLoop()
