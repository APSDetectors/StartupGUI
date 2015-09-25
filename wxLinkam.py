#!wxLinkam.py

#  wxLinkam.py
#  
#  This is a wxPython GUI to launch the
#  Linkam thermal stages.  
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 05/20/2013
#           08/08/2013
#			04/23/2014 - Simplified, added fixes for wxCallAfter
#			12/09/2014 - Changed how MEDMs starts
#			04/29/2015 - Added Quick Start Guide

import wx
import commands
import os
import signal
import subprocess
import time
import threading
import DPOStools as DPOStools
import sys
sys.path.append("/local/config/")
import xrd_config as xrd_config


# Constants
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000

pv_Prefix = xrd_config.DP_PV_SECTOR + 'linkam'+ xrd_config.DP_PV_SUFFIX

class LinkamFrame(wx.Frame):
	'''Linkam Window'''

	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP Linkam Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		#Set PS checking wait time
		self.checkCycle=0.01
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Linkam', '')				# Add entry
		wx.EVT_MENU(self, 101, self.helpDocs_101_Event)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar


		#--------------------------------------------------------------------------------------
		# Linkam
		#--------------------------------------------------------------------------------------
		self.title = wx.StaticText(self.background, label="Linkam")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# This Dictionary holds required information for each Process controlled by the GUI
		self.processes={
					'IOC':{	'pid': -999,
							'running': False,
							'search': 'EPLinkam1',
							'file': ['/local/DPbin/Scripts/start_ioc', 'linkam'],
							},
					'MEDM':{	'pid': -999,
								'running': False,
								'search': 'medm -x -attach -macro P='+pv_Prefix,
								'file': ['/local/DPbin/Scripts/start_medm_linkam', pv_Prefix],
								},	
					}

		# Start and Stop Buttons:
		self.ButtonOrder = [
							"IOC",
							"MEDM",
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
		# IOC
		self.Buttons['IOC']["Start Button"].Bind(wx.EVT_BUTTON, self.start_ioc_Event)
		self.Buttons['IOC']["Stop Button"].Bind(wx.EVT_BUTTON, self.stop_ioc_Event)

		# MEDM
		self.Buttons['MEDM']["Start Button"].Bind(wx.EVT_BUTTON, self.start_medm_Event)
		self.Buttons['MEDM']["Stop Button"].Bind(wx.EVT_BUTTON, self.stop_medm_Event)
		
	
		self.horizontalBoxes = []
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
		tempCommand = ['firefox', 'https://www1.aps.anl.gov/Divisions/XSD-Groups/Detectors/Sample-Environment']
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
			

	def start_ioc_Event(self, event):
		'''Start the IOC'''
		if not(self.processes['IOC']['running']):
			print "Starting IOC..."

			# Start the subprocess
			tempFile = self.processes['IOC']['file']
			self.IOCsubprocess = subprocess.Popen(tempFile, preexec_fn=os.setsid)

			# Grab the subprocess I.D.
			self.processes['IOC']['pid'] = DPOStools.waitforprocess(self.processes['IOC']['search'])
			self.processes['IOC']['running']=True
			
			# Set the Button Colour
			self.button_status('IOC', 'on')
		else:
			print "IOC already running!"

	def stop_ioc_Event(self, event):
		'''Kill the IOC'''
		if(self.processes['IOC']['running']):
			os.kill(self.processes['IOC']['pid'], signal.SIGTERM)
			self.button_status("IOC", 'off')
			print "IOC was stopped by user."
		else:
			print "No process to stop."


	def start_medm_Event(self, event):
		'''Start the MEDM'''
		if not(self.processes['MEDM']['running']):

			# Start the subprocess
			tempFile = self.processes['MEDM']['file']
			subprocess.Popen(tempFile, preexec_fn=os.setsid)

			# Grab the subprocess I.D.
			self.processes['MEDM']['pid'] = DPOStools.waitforprocess(self.processes['MEDM']['search'])
			self.processes['MEDM']['running']=True

			# Print self.pid_medm
			print "\nOpening MEDM..."

			# Set the Button Status
			self.button_status('MEDM', 'on')
		else:
			print "MEDM already running!"

	def stop_medm_Event(self, event):
		'''Kill the MEDM'''
		if(self.processes['MEDM']['running']):
			os.kill(self.processes['MEDM']['pid'], signal.SIGTERM)
			self.button_status("MEDM", 'off')
			print "MEDM was stopped by user."
		else:
			print "No process to stop."
		
	
	
#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

# Make an application
#app_2 = wx.App(redirect=False)

# Make an instance of the class - the Topmost GUI element
#startTest = StartFrame()
#russTest = LinkamFrame()

# Let it run!
#app_2.MainLoop()
