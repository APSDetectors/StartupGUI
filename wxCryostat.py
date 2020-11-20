#!wxCryostat.py

#  wxCryostat
#  
#  This is a wxPython GUI designed to launch EPICS IOC and MEDM
#  scripts on the new RHEL LDAP Detector Pool machines.  
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 05/20/2013
#           08/08/2013
#           03/12/2014
#           03/27/2014
#           07/17/2014
#           09/09/2014
#	    12/09/2014 - Updated pv_Prefix construction
#	    03/25/2015 - Added save restore menu & updated to newer way of button updateds
#	    04/29/2015 - Added Quick Start Guide, removed old wxSaveRestore code
#	    06/04/2019 - updated stop_Event and pscheck to work better with caQtDM

#import epics
import wx
import commands
import os
import signal
import subprocess
import time
import threading
import DPOStools_v3 as DPOStools
import xrd_config


WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000
DETECTOR = 'Cryostat'

#pv_Prefix = 'prosilica'
pv_Prefix = xrd_config.DP_PV_SECTOR + 'cryostat' + xrd_config.DP_PV_SUFFIX

class CryostatFrame(wx.Frame):
	'''Cryostat Window'''
	
	# Globals
	pid_ioc = -999
	pid_medm = -999
	pid_imagej = -999

	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'Cryostream 700 Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		#Set PS checking wait time
		self.checkCycle=0.1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Cryostream', '')				# Add entry
		wx.EVT_MENU(self, 101, self.helpDocs_101_Event)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar
		
		
		#--------------------------------------------------------------------------------------
		# Cryostream 700
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="Cryostream 700")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Model Name
		#self.ModelBox_title = wx.StaticText(self.background, -1, 'DP Prosilica \t\nModel Number:\t')
		#self.ModelBox_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		#self.ModelBox = wx.ComboBox(self.background, choices=["GC1380H", "GC2450", "XrayEye", "1BM_manta" ], size=[90,25])
		#self.ModelBox.SetEditable(False)
		
		# Bit Depth
		#self.BitDepthBox_title = wx.StaticText(self.background, -1, 'Bit Depth:\t')
		#self.BitDepthBox_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		#self.BitDepthBox = wx.ComboBox(self.background, choices=["8", "16"], size=[80,25])
		#self.BitDepthBox.SetEditable(False)

		# Launch and Stop Buttons:
		# This Dictionary holds required information for each Process controlled by the GUI
		self.processes={
					'IOC':{		'pid': -999,
								'running': False,
								'search': 'simDetectorApp',
								'file': '/local/DPbin/Scripts/start_ioc',
							  },
					'MEDM':{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P='+ pv_Prefix +'',
								'file': ['/local/DPbin/Scripts/start_medm_cryostat', pv_Prefix],
								},	
					'IMAGEJ':{	'pid': -999,
								'running': False,
								'search': 'jar ij.jar -run EPICS AD Viewer',
								'file': ['/local/DPbin/Scripts/start_imageJ', pv_Prefix],
							},
					'SAVE-RESTORE MENU':
							{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P='+ pv_Prefix +':,CONFIG=setup, configMenu_small.adl',
								'file': ['/local/DPbin/Scripts/start_medm_configMenu', pv_Prefix],
							},
					'caQtDM':
					    {	'pid': -999,
								'running': False,
								'search': 'caQtDM -macro P='+pv_Prefix +':, C=CS: CryoStream700.ui',
								'file': ['/local/DPbin/Scripts/start_caQtDM_cryostat',pv_Prefix,]
							},
					}


		# Start and Stop Buttons:
		self.ButtonOrder = [
							"IOC",
							"MEDM",
							#'IMAGEJ',
							'SAVE-RESTORE MENU',
							'caQtDM',
							]
						
		self.Buttons = dict.fromkeys(self.ButtonOrder)
		
		# Create Buttons and labels
		for Row in self.ButtonOrder:
			self.Buttons[Row] = dict.fromkeys(["Title", "Start Button", "Stop Button"])
			self.Buttons[Row]["Title"] = wx.StaticText(self.background, label=Row + " \t")
			self.Buttons[Row]["Title"].SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
			self.Buttons[Row]["Start Button"] = wx.Button(self.background, label='Start', size=[60,25])
			self.Buttons[Row]["Stop Button"] = wx.Button(self.background, label='Stop', size=[60,25])
		
		# Bind buttons to functions 
		self.Buttons['IOC']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IOC'))
		self.Buttons['IOC']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IOC'))
		self.Buttons['MEDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MEDM'))
		self.Buttons['MEDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MEDM'))	
		#self.Buttons['IMAGEJ']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IMAGEJ'))
		#self.Buttons['IMAGEJ']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IMAGEJ'))
		self.Buttons['SAVE-RESTORE MENU']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['SAVE-RESTORE MENU']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['caQtDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'caQtDM'))
		self.Buttons['caQtDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'caQtDM'))			
	
		
		
		# Make Horizontal Box Sizers
		self.horizontalBoxes = []
		
		#self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
		#self.horizontalBoxes[-1].Add(self.ModelBox_title, proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
		#self.horizontalBoxes[-1].Add(self.ModelBox, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		
		#self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
		#self.horizontalBoxes[-1].Add(self.BitDepthBox_title, proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
		#self.horizontalBoxes[-1].Add(self.BitDepthBox, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		
		
		for Rows in self.ButtonOrder:
			self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Title'], proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Start Button'], proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Stop Button'], proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		
		
		# Make a vertical sizer
		self.verticalBox = wx.BoxSizer(wx.VERTICAL)
		self.verticalBox.Add(self.title, proportion = 0, border = 1, flag=wx.ALIGN_CENTER)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)
		self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)
		
		
		for Row in self.horizontalBoxes:
			 self.verticalBox.Add(Row, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
			 self.verticalBox.Add(wx.StaticLine(self.background, -1, style=wx.LI_HORIZONTAL), proportion=0, flag=wx.EXPAND)

		# PS checking
		self.progRunning = True
		self.PSthread = threading.Thread(target=self.pscheck)
		self.PSthread.start()
		
		# Set the panel size
		self.background.SetSizer(self.verticalBox)
		self.background.Fit()
		self.Fit()
		self.Show()


	#--------------------------------------------------------------------------------------
	# Define Event Methods (button actions)
	#--------------------------------------------------------------------------------------

	def helpDocs_101_Event(self, event):
		tempCommand = ['firefox', 'https://www.aps.anl.gov/Detectors/Sample-Environment#CryoStream']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)

	def start_Event(self, event, app):
		'''Start an App'''
		if not(self.processes[app]['running']):
			print 'Starting ' + str(app) + '...'
			# Start the subprocess
			if app == 'IOC':
				CCD = 'Cryostat'
				#CCD = self.ModelBox.GetValue()
				#BitDepth = self.BitDepthBox.GetValue()
				#if len(CCD)>0 and len(BitDepth)>0:	
				# Start the IOC
			
				# Start the subprocess
				#tempFile = [self.processes['IOC']['file'], str(CCD) + "-" + str(BitDepth)]
				tempFile = [self.processes['IOC']['file'], str(CCD)]
				self.IOCsubprocess = subprocess.Popen(tempFile, preexec_fn=os.setsid)

				# Grab the subprocess I.D.
				self.processes['IOC']['pid'] = DPOStools.waitforprocess(self.processes['IOC']['search'])
				self.processes['IOC']['running'] = True
				self.button_status(app, 'on')
				print 'process id ' + str(app) + ' = ' + str(self.processes[app]['pid'])
			else:
			
				subprocess.Popen(self.processes[app]['file'], preexec_fn=os.setsid)
			
				# Grab the subprocess I.D.
				self.processes[app]['pid'] = DPOStools.waitforprocess(self.processes[app]['search'])
				self.processes[app]['running']=True
				# Set the button state
				self.button_status(app, 'on')
				print 'process id ' + str(app) + ' = ' + str(self.processes[app]['pid'])
		else:
			print str(app)+' already running!'

	def stop_Event(self, event, app):
		'''Stop an App'''
		if(self.processes[app]['running']):
			print 'Stopping '+str(app)+'...'

			# pgrep for all associated PIDs and make into a list
			pids = (subprocess.check_output([ 'pgrep', '-f', self.processes[app]['search'] ])).split('\n')
			pids = filter(None, pids)

			# Loop over all PIDs
			for i in pids:
				print ' stopping pid: ' + str(i)
				os.kill(int(i), signal.SIGKILL)

			self.button_status(app, 'off')
		else:
			print "No process to stop."

	def pscheck(self):
		'''Track the current state of processes - Runs in a separate thread'''
		while(self.progRunning):
			for item in self.processes:
				#print 'pscheck is running: ' + str(item)
				try:
					tempResult = subprocess.check_output([ 'pgrep', '-f', self.processes[item]['search'] ])
					self.processes[item]['pid'] = int(tempResult.split('\n')[0])
					if not(self.processes[item]['running']):
						self.button_status(item, 'on')
						self.processes[item]['running'] = True
				except:
					if(self.processes[item]['running']):
						self.button_status(item, 'off')
			time.sleep(self.checkCycle)


	def button_status(self, app, switch):
		'''Change a button status'''
		if switch == 'on':
			#print 'setting button colour and label'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetBackgroundColour, wx.GREEN)
			wx.CallAfter(self.Buttons[app]['Start Button'].SetLabel, "Running")

		elif switch == 'off':
			if app in self.processes:
				print 'switching the button OFF...'
				self.processes[app]['pid'] = -999
				self.processes[app]['running'] = False
			#print 'setting button colour and label'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetBackgroundColour, wx.WHITE)
			wx.CallAfter(self.Buttons[app]['Start Button'].SetLabel, "Start")


	def OnClose(self, event):
		'''This method Prompts the User for confimation when closing the Window'''
		if self.closeprompt:
			dlg = wx.MessageDialog(self,"Close the GUI?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			result = dlg.ShowModal()
			dlg.Destroy()
		else:
			result = wx.ID_OK
		if result == wx.ID_OK:
			# Clean up PSthread
			self.progRunning=False
			while (self.PSthread.isAlive()):
				time.sleep(self.checkCycle)	
			self.Hide()
			

#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

# Make an application
#app_2 = wx.App(redirect=False)

# Make an instance of the class - the Topmost GUI element
#russTest = PilatusFrame()

# Let it run!
#app_2.MainLoop()

