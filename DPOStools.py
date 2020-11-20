#! DPOStools.py

# Update 2015-01-20 	Adding function to find what beamline we are at
# Update 2015-03-23		Adding function to return number of copies of process running on machine
# Update 2015-09-25   Removed save restore stuff
# Update 2017-01-11		REALLY removed save restore stuff!


import subprocess
import time
import os
from socket import gethostname, gethostbyname

#-------------------------------------------------------------------
def waitforprocess(processCMD):
	'''Waits for Process to start, returns I.D.'''
	while True:
		#find the PID, the hard way
		try:
			psresults=subprocess.check_output(["pgrep", "-f", processCMD])
			break
		except:
                        print 'waiting for process to start...'
			time.sleep(1)
	#print 'DPOStools_v2 psresults = ' + str(psresults) 		
	return int(psresults.split('\n')[0])

#-------------------------------------------------------------------
def processCount(processCMD):
	'''Waits for Process to start, returns I.D.'''
	while True:
		#find the PID, the hard way
		try:
			psresults=subprocess.check_output(["pgrep", "-f", processCMD])
			break
		except:
			time.sleep(0.1)
	#print 'DPOStools_v2 psresults = ' + str(psresults) 		
	return len(psresults.split('\n'))
	
#-------------------------------------------------------------------	
def findSector():
	host = gethostname()
	ip = gethostbyname(host)
	subnet = int(ip.split('.')[2])
	
	if subnet in [101, 85, 84]:
		return 'DP'
	elif subnet in [112]:
		return 's1'
	elif subnet in [113]:
		return 's2'
	elif subnet in [114]:
		return 's3'
	elif subnet in [115]:
		return 's4'
	elif subnet in [148, 149]:
		return 's5'
	elif subnet in [106]:
		return 's6'
	elif subnet in [107]:
		return 's7'
	elif subnet in [108, 116]:
		return 's8'
	elif subnet in [112]:
		return 's9'
	elif subnet in [244]:
		return 's10'
	elif subnet in [111]:
		return 's11'
	elif subnet in [122]:
		return 's12'
	elif subnet in [160]:
		return 's13'
	elif subnet in [161]:
		return 's14'
	elif subnet in [162]:
		return 's15'
	elif subnet in [164]:
		return 's16'
	elif subnet in [200]:
		return 's17'
	elif subnet in [204]:
		return 's18'
	elif subnet in [192, 193]:
		return 's19'
	elif subnet in [119]:
		return 's20'
	elif subnet in [252]:
		return 's21'
	elif subnet in [208]:
		return 's22'
	elif subnet in [103, 210]:
		return 's23'
	elif subnet in [212, 213]:
		return 's24'	
	elif subnet in []:
		return 's25'
	elif subnet in [128]:
		return 's26'
	elif subnet in [126]:
		return 's27'
	elif subnet in []:
		return 's28'
	elif subnet in [118]:
		return 's29'
	elif subnet in [103, 210]:
		return 's30'
	elif subnet in [214]:
		return 's31'	
	elif subnet in [102]:
		return 's32'
	elif subnet in [124, 125]:
		return 's33-34'
	elif subnet in [235]:
		return 's35'
	else:
		return 'unknown'
#-------------------------------------------------------------------	

	
