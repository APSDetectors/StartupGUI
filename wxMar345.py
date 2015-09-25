#!wxMar345.py

#  wxMar345.py
#  
#  This is a wxPython GUI designed to launch EPICS IOC and MEDM
#  scripts on the new RHEL LDAP Detector Pool machines.  
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 5/20/2013
#           8/8/2013
#	        9/16/2014
#			12/09/2014 - changed how MEDM & ImageJ start
#			04/29/2015 - Added Quick Start Guide, removed old wxSaveRestore code

import wx
import commands
import os
import signal
import subprocess
import time
import threading
import DPOStools
import sys

sys.path.append("/local/config/")
import xrd_config as xrd_config

# Constants
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000

pv_Prefix = xrd_config.DP_PV_SECTOR + 'mar345'+ xrd_config.DP_PV_SUFFIX

class Mar345Frame(wx.Frame):
	"""Mar345 Window"""

	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP Mar345 Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		#Set PS checking wait time
		self.checkCycle=0.1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Mar345', '')				# Add entry
		wx.EVT_MENU(self, 101, self.helpDocs_101_Event)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar


		#--------------------------------------------------------------------------------------
		# Mar345
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="Mar345")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Scanner number
		self.scannerBox_title = wx.StaticText(self.background, -1, 'Scanner Number:')
		self.scannerBox_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.scannerBox = wx.TextCtrl(self.background, size=[60,25])
		
		# Launch and Stop Buttons:
		# This Dictionary holds required information for each Process controlled by the GUI
		self.processes={
					'IOC':{	'pid': -999,
							'running': False,
							'search': 'mar345App',
							'file': ['/local/DPbin/Scripts/start_ioc','mar345'],
							},
					'MEDM':{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P='+ pv_Prefix + ':, R=cam1: mar345.adl',
								'file': ['/local/DPbin/Scripts/start_medm_mar345', pv_Prefix],
								},	
					'ImageJ':{	'pid': -999,
							'running': False,
							'search': 'jar ij.jar -run EPICS AD Viewer',
							'file': ['/local/DPbin/Scripts/start_imageJ', pv_Prefix],
							},
					'MarDTB':{	'pid': -999,
							'running': False,
							'search': '/local/DPbin/mar345/bin/mar345dtb',
							'file': '/local/DPbin/Scripts/start_mar345dtb',
							},
					'SAVE-RESTORE MENU':
							{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P='+ pv_Prefix +':,CONFIG=setup, configMenu_small.adl',
								'file': ['/local/DPbin/Scripts/start_medm_configMenu',pv_Prefix,]
							},
					'caQtDM':
					    {	'pid': -999,
								'running': False,
								'search': 'caQtDM -macro P='+ pv_Prefix + ':, R=cam1: mar345.ui',
								'file': ['/local/DPbin/Scripts/start_caQtDM_mar345',pv_Prefix,]
							},
					
					}

		# Start and Stop Buttons:
		self.ButtonOrder = [
							'MarDTB',
							'IOC',
							'MEDM',
							'ImageJ',
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
		self.Buttons['ImageJ']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'ImageJ'))
		self.Buttons['ImageJ']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'ImageJ'))
		self.Buttons['MarDTB']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MarDTB'))
		self.Buttons['MarDTB']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MarDTB'))
		self.Buttons['SAVE-RESTORE MENU']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['SAVE-RESTORE MENU']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['caQtDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'caQtDM'))
		self.Buttons['caQtDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'caQtDM'))	
		
		# Make Horizontal Box Sizers
		self.horizontalBoxes = []
		
		self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
		self.horizontalBoxes[-1].Add(self.scannerBox_title, proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
		self.horizontalBoxes[-1].Add(self.scannerBox, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		
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
	#         NOTE: Executed scripts MUST have a shebang! definition in line #1
	#--------------------------------------------------------------------------------------	
	def helpDocs_101_Event(self, event):
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Mar_345_Image_Plate/index.html']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
		
	def pscheck(self):
		'''Track the current state of processes - Runs in a separate thread'''
		global DetectorThreadRunning
		while(self.progRunning):
			#print self.checkbox1.GetValue()
			for item in self.processes:
				#print 'item =' + str(item)
				#print 'pscheck is running...'
				try:
					tempResult = subprocess.check_output([ 'pgrep', '-f', self.processes[item]['search'] ])
					self.processes[item]['pid'] = int(tempResult)
					if not(self.processes[item]['running']):
						self.button_status(item, 'on')
						self.processes[item]['running'] = True
				except:
					if(self.processes[item]['running']):
						#print 'program ended, calling button_status...'
						self.button_status(item, 'off')
						#print '...button_status update finished
			
			time.sleep(self.checkCycle)

	def button_status(self, app, switch):
		if switch == 'on':
			#print 'setting button colour = green'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetBackgroundColour, wx.GREEN)
			#print 'setting buttton label = Running'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetLabel, "Running")

		elif switch == 'off':
			if app in self.processes:
				#print 'setting pid = -999'
				self.processes[app]['pid'] = -999
				#print 'setting running = False'
				self.processes[app]['running'] = False
			#print 'setting button colour = white'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetBackgroundColour, wx.WHITE)
			#print 'setting button label = start'
			wx.CallAfter(self.Buttons[app]['Start Button'].SetLabel, "Start")
	
	
	def OnClose(self, event):
		'''This method Prompts the User for confimation when closing the Window'''
		if self.closeprompt:
			dlg = wx.MessageDialog(self,"Do you really want to close this app?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			result = dlg.ShowModal()
			dlg.Destroy()
		else:
			result = wx.ID_OK

		if result == wx.ID_OK:		
			# Cleans up PSthread
			self.progRunning = False
			self.PSthread.join()
			while (self.PSthread.isAlive()):
				time.sleep(self.checkCycle)
					
			self.Hide()
	
		
	def start_Event(self, event, app):
		'''Start an App'''
		if not(self.processes[app]['running']):
			print 'Starting ' + str(app) + '...'
			# Start the subprocess
			tempCommand = self.processes[app]['file']
			
			if app=='MarDTB':
				Scanner = self.scannerBox.GetValue()
				if len(Scanner)>0:
					tempCommand = [self.processes['MarDTB']['file'], str(Scanner)]
				
					# Start the subprocess
					subprocess.Popen(tempCommand, preexec_fn=os.setsid)
					
			else:
				subprocess.Popen(tempCommand, preexec_fn=os.setsid)
			
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
			os.kill(self.processes[app]['pid'], signal.SIGKILL)
			self.button_status(app, 'off')
		else:
			print "No process to stop."
	
	
#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

# Make an application
#app_2 = wx.App(redirect=False)

# Make an instance of the class - the Topmost GUI element
#startTest = StartFrame()
#russTest = Mar345Frame()

# Let it run!
#app_2.MainLoop()
