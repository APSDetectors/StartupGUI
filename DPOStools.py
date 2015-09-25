#! DPOStools.py

import subprocess
import time

def waitforprocess(processCMD):
	while True:
		#find the PID, the hard way
		try:
			psresults=subprocess.check_output(["pgrep", "-f", processCMD])
			break
		except:
			time.sleep(1)

	
	return int(psresults)
