# file : wxMerlin_v1.py

#!/APSshare/epd/rh6-x86/bin/python2.7

#  wxMerlin_v1.py
#  
#  This is a wxPython GUI to launch the
#  Quantum Detectors Merlin
#
#  Authors: Russell Woods, Matthew Moore
#     Date: 02/20/2015 Copied from wxPixirad_v2.py
#           

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
WINDOW_HEIGHT = 10
DETECTOR = 'merlin'
pv_Prefix = xrd_config.DP_PV_SECTOR + 'merlin'+ xrd_config.DP_PV_SUFFIX

class MerlinFrame(wx.Frame):
	'''Merlin Window'''
	
	# Define Self Method
	def __init__(self, position=(400,500), parent=None, ClosePrompt=False, SaveRestore=False):
		wx.Frame.__init__(self, parent, title = 'Merlin Startup', pos = position, size = (WINDOW_WIDTH, WINDOW_HEIGHT), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		# Set PS checking wait time (seconds)
		self.checkCycle=1
		
		# Make the panel
		self.background = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		
		# Add a 'OnClose' Message Prompt
		self.closeprompt=ClosePrompt
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		#--------------------------------------------------------------------------------------
		# Neo
		#--------------------------------------------------------------------------------------
		self.processes = {	'IOC':{	'pid': -999,
								'running': False,
								'search': '../../bin/linux-x86_64/merlin st.cmd',
								'file': ['/local/DPbin/Scripts/start_ioc', 'merlin'],
							},
							'MEDM':{'pid': -999,
								'running': False,
								'search': 'ADMerlinQuad.adl',
								'file': '/local/DPbin/Scripts/start_medm_merlinQuad',
							},
							'IMAGEJ':{'pid': -999,
								'running': False,
								'search': './jre/bin/java -Xmx1024m -jar ij.jar -run EPICS AD Viewer',
								'file': '/local/DPbin/Scripts/start_imageJ',
							},
		}
		
		# Title:									
		self.title = wx.StaticText(self.background, label="Merlin Quad")
		self.title.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Start and Stop Buttons:
		self.ButtonOrder = ['IOC',
							'MEDM',
							'IMAGEJ',
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
	
		self.Buttons['IOC']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IOC'))
		self.Buttons['IOC']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IOC'))
		self.Buttons['MEDM']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'MEDM'))
		self.Buttons['MEDM']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'MEDM'))	
		self.Buttons['IMAGEJ']['Start Button'].Bind(wx.EVT_BUTTON, lambda event: self.start_Event(event, 'IMAGEJ'))
		self.Buttons['IMAGEJ']['Stop Button'].Bind(wx.EVT_BUTTON, lambda event: self.stop_Event(event, 'IMAGEJ'))
	
	
		# SaveRestore Buttons
		if SaveRestore:
			self.restore_title = wx.StaticText(self.background, label="Save/Restore Manager\t")
			self.restore_title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
			self.restore_Btn = wx.Button(self.background, label = 'Open', size=[60,25])
			self.restore_Btn.Bind(wx.EVT_BUTTON, self.restore_Event)
											
		# Make Horizontal Box Sizers
		self.horizontalBoxes = []							
		for Rows in self.ButtonOrder:
			self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Title'], proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Start Button'], proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
			self.horizontalBoxes[-1].Add(self.Buttons[Rows]['Stop Button'], proportion = 0, border = 0,flag=wx.ALIGN_CENTER)
		if SaveRestore:
			self.horizontalBoxes.append(wx.BoxSizer(wx.HORIZONTAL))
			self.horizontalBoxes[-1].Add(self.restore_title, proportion = 1, border = 0,flag=wx.ALIGN_CENTER)
			self.horizontalBoxes[-1].Add(self.restore_Btn, proportion = 0, border = 0,flag=wx.ALIGN_CENTER)					
							
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

	def start_Event(self, event, app):
		'''Start an App'''
		if not(self.processes[app]['running']):
			print 'Starting ' + str(app) + '...'
			# Start the subprocess
			tempCommand = self.processes[app]['file']
			
			if app=='MEDM' or app=='IMAGEJ':
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


	def restore_Event(self, event):
		'''Launch Save/Restore Window'''
		print 'Opening save/restore window...'
		self.child = wxSaveRestore.saveRestoreFrame(parent=self)
		self.child.Center()
		self.child.Show()
		self.child.detectorBox.SetValue(DETECTOR)


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
			
'''
#---------------------------------------------------------------------------------
#  Main loop
#---------------------------------------------------------------------------------

# Make an application
app_2 = wx.App(redirect=False)

# Make an instance of the class - the Topmost GUI element
russTest = PixiradFrame()

# Let it run!
app_2.MainLoop()
'''
