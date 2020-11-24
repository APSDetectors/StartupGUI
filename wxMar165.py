# file : wxMar165.py

#  wxMar165.py
#  
#  This is a wxPython GUI to launch the
#  Mar165 CCD scripts  
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 05/20/2013
#		08/21/2013
#		05/05/2014 - Move to standardized setup and fixed bug related to wx.callafter
#		09/04/2014
#		04/29/2015 - Added Quick Start Guide, removed old wxSaveRestore code
#		10/13/2017 - Added field for entering the detector serial number, used to load correct calibration file
#	        06/04/2019 - updated stop_Event and pscheck to work with caQtDM from APSshare

import wx
import commands
import os
import signal
import subprocess
import time
import threading


# Get DPOStools
import sys
import DPOStools

sys.path.append("/local/config/")
import xrd_config as xrd_config

# Constants
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000

#pv_Prefix = 'dp_mar165_'
pv_Prefix = xrd_config.DP_PV_SECTOR + 'mar165' + xrd_config.DP_PV_SUFFIX

class Mar165Frame(wx.Frame):
	"""Mar165 Window"""

	# Globals:
	MODEL_CHOICE = -999

	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP Mar 165 Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		# Set PS checking wait time (seconds)
		self.checkCycle=1

		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		
		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Mar165', '')				# Add entry
		self.Bind(wx.EVT_MENU, self.helpDocs_101_Event, id=101)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar

		#--------------------------------------------------------------------------------------
		# Mar165 CCD
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="Mar165")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# serial number entry
		MARCCD_LIST = ['DetPool A :0062', 'DetPool B :0069', 'DetPool C :0022', 'Sector 12 :0040', 'HPCAT :0087',]
		self.serialBox_title = wx.StaticText(self.background, -1, 'Detector Serial Number:')
		self.serialBox_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		#self.serialBox = wx.TextCtrl(self.background, size=[60,25])
		self.serialBox = wx.ComboBox(self.background, -1, "choose detector ID", size=(250,25), choices=MARCCD_LIST, style=wx.CB_READONLY)

		# Launch and Stop Buttons:
		# This Dictionary holds required information for each Process controlled by the GUI
		self.processes={
					'IOC':{	'pid': -999,
							'running': False,
							'search': 'marCCDApp st.cmd',
							'file': ['/local/DPbin/Scripts/start_ioc', 'mar165']
							},
					'MEDM':{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P=' + pv_Prefix + ':, R=cam1: marCCD.adl',
								'file': '/local/DPbin/Scripts/start_medm_mar165',
								},	
					'IMAGEJ':{	'pid': -999,
								'running': False,
								'search': 'jar ij.jar -run EPICS AD Viewer',
								'file': '/local/DPbin/Scripts/start_imageJ',
								},
					'MARCCD':{	'pid': -999,
								'running': False,
								'search': "/opt/marccd/bin/marccd",
								'file': ['/local/DPbin/Scripts/start_marccd'],
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
								'search': 'caQtDM -macro P='+ pv_Prefix + ':, R=cam1: marCCD.ui',
								'file': ['/local/DPbin/Scripts/start_caQtDM_mar165',pv_Prefix,]
							},
					}

		# Start and Stop Buttons:
		self.ButtonOrder = [
					'MARCCD',
					'IOC',
					'MEDM',
					'IMAGEJ',
					'SAVE-RESTORE MENU',
					'caQtDM',
					]
			
		self.Buttons = dict.fromkeys(self.ButtonOrder)

		# Create Buttons, Labels, and Bindings:
		for Row in self.ButtonOrder:
			self.Buttons[Row] = dict.fromkeys(["Title", "Start Button", "Stop Button"])
			self.Buttons[Row]["Title"] = wx.StaticText(self.background, label=Row + " \t")
			self.Buttons[Row]["Title"].SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
			self.Buttons[Row]["Start Button"] = wx.Button(self.background, label='Start', size=[60,25])
			self.Buttons[Row]["Stop Button"] = wx.Button(self.background, label='Stop', size=[60,25])
	
		self.Buttons['IOC']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IOC'))
		self.Buttons['IOC']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IOC'))
		self.Buttons['MEDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MEDM'))
		self.Buttons['MEDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MEDM'))	
		self.Buttons['IMAGEJ']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IMAGEJ'))
		self.Buttons['IMAGEJ']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IMAGEJ'))
		self.Buttons['MARCCD']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MARCCD'))
		self.Buttons['MARCCD']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MARCCD'))
		self.Buttons['SAVE-RESTORE MENU']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['SAVE-RESTORE MENU']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['caQtDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'caQtDM'))
		self.Buttons['caQtDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'caQtDM'))			
	
											
		# Make Horizontal Box Sizers
		self.horizontalBoxes = []
		self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
		self.horizontalBoxes[-1].Add(self.serialBox_title, proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
		self.horizontalBoxes[-1].Add(self.serialBox, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		
						
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
		self.progRunning=True
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
		tempCommand = ['firefox', 'http://www.aps.anl.gov/Xray_Science_Division/Detectors/Detector_Pool/Detector_Information/Mar_165_CCD_Camera/index.html']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
		
	def start_Event(self, event, app):
		'''Start an App'''
		if not(self.processes[app]['running']):
			print 'Starting ' + str(app) + '...'
			# Start the subprocess
			tempCommand = self.processes[app]['file']
			
			if app=='MARCCD':
				serialNum = self.serialBox.GetValue().split(':')[1]
				print 'Detector Choice = ' + serialNum + '\n'
				if len(serialNum)==4:
					tempCommand = [self.processes['MARCCD']['file'], str(serialNum)]
					subprocess.Popen(tempCommand, preexec_fn=os.setsid)
				else:
					print "Please Choose CCD from dropdown menu"

			elif app=='MEDM' or app=='IMAGEJ':
				subprocess.Popen([tempCommand, pv_Prefix], preexec_fn=os.setsid)
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
				try:
					tempResult = (subprocess.check_output([ 'pgrep', '-f', self.processes[item]['search'] ])).split('\n')[0]
					self.processes[item]['pid'] = int(tempResult)
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
				

