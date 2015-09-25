# file : wxPilatus.py

#!/APSshare/epd/rh6-x86/bin/python2.7

#  wxPilatus.py
#  
#  This is a wxPython GUI to launch the
#  Dectris Pilatus 100k
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 11/25/2013
#           12/18/2013
#	        04/07/2014
#	        05/14/2014
#			12/10/2014 - updating pv_config construction
#			01/20/2015 - Added save-restore menu
#			04/29/2015 - Added Quick Start Guide, removed old wxSaveRestore code
#     09/03/2015 - Added caQtDM

import wx
import commands
import os
import signal
import subprocess
import time
import threading


# Get DPOStools
import sys
sys.path.append("/local/config")
import DPOStools
import xrd_config


# Constants
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 1000
DETECTOR = 'Pilatus'
pv_Prefix = xrd_config.DP_PV_SECTOR + 'pilatus' + xrd_config.DP_PV_SUFFIX

class PilatusFrame(wx.Frame):
	'''Pilatus Window'''
	
	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False):
		wx.Frame.__init__(self, parent, title = 'DP Pilatus Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		# Set PS checking wait time (seconds)
		self.checkCycle=1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		self.closeprompt=ClosePrompt							# Add a 'OnClose' Message Prompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		
		# Make a Menu Bar
		self.menubar = wx.MenuBar()
		self.helpDocs = wx.Menu()								# Make a Menu
		self.helpDocs.Append(101, '&Pilatus', '')				# Add entry
		wx.EVT_MENU(self, 101, self.helpDocs_101_Event)			# Bind to Event
		self.menubar.Append(self.helpDocs, '&Help Documents')	# Append to Menu Bar
		self.SetMenuBar(self.menubar)							# Set Menu Bar


		#--------------------------------------------------------------------------------------
		# Pilatus 100k
		#--------------------------------------------------------------------------------------
		self.processes = {'CAMSERVER':	{'pid': -999,
						'running': False,
						'search': 'camserver',
						'file': ['/home/det/start_camonly',],
				},
				'IOC':{	'pid': -999,
					'running': False,
					'search': 'pilatusDetectorApp',
					'file': ['/local/DPbin/Scripts/start_ioc','pilatus100k']
				},
				'MEDM':{'pid': -999,
					'running': False,
					'search': 'medm -x -macro P='+ pv_Prefix +':, R=cam1: pilatusDetector.adl',
					'file': ['/local/DPbin/Scripts/start_medm_pilatus',pv_Prefix],
				},
				'IMAGEJ':{'pid': -999,
					'running': False,
					'search': './jre/bin/java -Xmx1024m -jar ij.jar -run EPICS AD Viewer',
					'file': ['/local/DPbin/Scripts/start_imageJ', pv_Prefix],
				},
				'SAVE-RESTORE MENU':{'pid': -999,
					'running': False,
					'search': 'medm -x -macro P='+ pv_Prefix +':,CONFIG=setup, configMenu_small.adl',
					'file': ['/local/DPbin/Scripts/start_medm_configMenu',pv_Prefix,]
				},
				'caQtDM':
					    {	'pid': -999,
								'running': False,
								'search': 'caQtDM -macro P='+ pv_Prefix + ':, R=cam1: pilatusDetector.ui',
								'file': ['/local/DPbin/Scripts/start_caQtDM_pilatus',pv_Prefix,]
							},
		}
		
		# Title:									
		self.title = wx.StaticText(self.background, label="Pilatus 100k")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Start and Stop Buttons:
		self.ButtonOrder = ['CAMSERVER',
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
			#self.Buttons[Row]['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, Row))  # <--------- Doesn't work for unknown reason.
			#self.Buttons[Row]['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, Row))
	
		self.Buttons['CAMSERVER']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'CAMSERVER'))
		self.Buttons['CAMSERVER']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'CAMSERVER'))	
		self.Buttons['IOC']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IOC'))
		self.Buttons['IOC']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IOC'))
		self.Buttons['MEDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MEDM'))
		self.Buttons['MEDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MEDM'))	
		self.Buttons['IMAGEJ']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IMAGEJ'))
		self.Buttons['IMAGEJ']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IMAGEJ'))
		self.Buttons['SAVE-RESTORE MENU']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['SAVE-RESTORE MENU']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'SAVE-RESTORE MENU'))
		self.Buttons['caQtDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'caQtDM'))
		self.Buttons['caQtDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'caQtDM'))			
	
											
		# Make Horizontal Box Sizers
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
		tempCommand = ['firefox', 'https://www1.aps.anl.gov/Divisions/XSD-Groups/Detectors/Area-Detectors#Pilatus']
		p_ioc = subprocess.Popen(tempCommand, shell=False, preexec_fn=os.setsid)
		
	def start_Event(self, event, app):
		'''Start an App'''
		if not(self.processes[app]['running']):
			print 'Starting ' + str(app) + '...'
			
			# Start the subprocess
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
			os.kill(self.processes[app]['pid'], signal.SIGKILL)
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

