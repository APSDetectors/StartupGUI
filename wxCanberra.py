#!wxCanberra.py

#  wxCanberra.py
#  
#  This is a wxPython GUI designed to launch EPICS IOC and MEDM
#  scripts on RHEL LDAP Detector Pool machines.  
#
#  Authors: Russell Woods, Matthew Moore
#	  Date: 5/20/2013
#		8/8/2013
#		04/23/2014 - Simplified, added fixes for wxCallAfter
#		12/09/2014 - changed MEDM startup 
#		04/29/2015 - Added Quick Start Guide, removed old wxSaveRestore code
#	    	06/04/2019 - updated stop_Event and pscheck to work with caQtDM from APSshare

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

pv_Prefix = xrd_config.DP_PV_SECTOR + 'Canberra'+ xrd_config.DP_PV_SUFFIX

# Declare constants in capitals and as global variables at the start of your code
# This makes it much easier to change them later, especially if they are used often.
# It also indicates they are values that won't change throughout the programme's execution.

WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000

class CanberraFrame(wx.Frame):
	"""Canberra Window"""

	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP Canberra Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		#Set PS checking wait time
		self.checkCycle=1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Canberra', '')				# Add entry
		self.Bind(wx.EVT_MENU, self.helpDocs_101_Event, id=101)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar
		

		#--------------------------------------------------------------------------------------
		# Vortex
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="Canberra Negative High Voltage")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		
		# PreAmp Frequency:
		self.saturn_title = wx.StaticText(self.background, -1, 'SATURN BOX')
		self.saturn_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.saturn_entry = wx.ComboBox(self.background, choices=["20MHz_negative", "40MHz_negative"], size=[150,25])
		self.saturn_entry.SetEditable(False)
		self.saturn_entry.SetValue("20MHz_negative")
		
		
		# This Dictionary holds required information for each Process controlled by the GUI
		self.processes={
					'IOC':{	'pid': -999,
							'running': False,
							'search': 'dxpApp',
							'file': '/local/DPbin/Scripts/start_ioc',
							},
					'MEDM':{	'pid': -999,
								'running': False,
								'search': 'medm -x -macro P='+pv_Prefix+':, D=dxp1:, M=mca1 dxpSaturn.adl',
								'file': ['/local/DPbin/Scripts/start_medm_Canberra', pv_Prefix],
								},	
					'IDL MCA':{	'pid': -999,
								'running': False,
								'search': "vm=/local/DPbin/MCA/mca.sav",
								'file': '/local/DPbin/Scripts/start_idl_mca',
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
								'search': 'caQtDM -macro P='+ pv_Prefix + ':,D=dxp1:,M=mca1 dxpSaturn.ui',
								'file': ['/local/DPbin/Scripts/start_caQtDM_vortex',pv_Prefix,]
							},
					
					}

		# Start and Stop Buttons:
		self.ButtonOrder = [
							"IOC",
							"MEDM",
							'IDL MCA',
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
		self.Buttons['IDL MCA']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IDL MCA'))
		self.Buttons['IDL MCA']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IDL MCA'))
		self.Buttons['SAVE-RESTORE MENU']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['SAVE-RESTORE MENU']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['caQtDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'caQtDM'))
		self.Buttons['caQtDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'caQtDM'))			
	
		
		# Make Horizontal Box Sizers
		self.horizontalBoxes = []
		self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
		self.horizontalBoxes[-1].Add(self.saturn_title, proportion = 1, border = 5,flag=wx.ALIGN_CENTER)
		self.horizontalBoxes[-1].Add(self.saturn_entry, proportion = 0, border = 5,flag=wx.ALIGN_CENTER)
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
		tempCommand = ['firefox', 'https://www1.aps.anl.gov/Detectors/Spectroscopic-Detectors#Ge']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
		
		
	def pscheck(self):
		'''Track the current state of processes - Runs in a separate thread'''
		global DetectorThreadRunning
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
			
			if app=='IOC':
				SaturnBoxChoice = self.saturn_entry.GetValue()
				tempFile = [self.processes['IOC']['file'], 'Canberra' + '-' + str(SaturnBoxChoice)]
				subprocess.Popen(tempFile, preexec_fn=os.setsid)
					
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

	
	
