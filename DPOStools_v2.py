#! DPOStools_v2.py

import subprocess
import time
#import epics.autosave
import os
import pyparsing
import save_restore

def waitforprocess(processCMD):
	'''Waits for Process to start, returns I.D.'''
	while True:
		#find the PID, the hard way
		try:
			psresults=subprocess.check_output(["pgrep", "-f", processCMD])
			break
		except:
			time.sleep(1)
	#print 'DPOStools_v2 psresults = ' + str(psresults) 		
	return int(psresults.split('\n')[0])


def savePVs(filePath, reqChoice, fileChoice):
	'''Use pyEpics to save PVs for a given sector/detector'''
	
	saveRestoreString = str(filePath) + str(fileChoice)
	reqString = str(filePath) + str(reqChoice)
	
	if(reqChoice and fileChoice):
		print '...saving PVs to: ' + str(filePath)
		#epics.autosave.save_pvs(reqString, saveRestoreString, True)
		save_restore.save_pvs(reqString, saveRestoreString, True)
	else:
		print 'Please choose both .req and .sav files!'


def restorePVs(filePath, fileChoice):
	'''Use pyEpics to restore PVs for a given sector/detector'''	

	saveRestoreString = str(filePath) + str(fileChoice)	
	print '...restoring PVs from: ' + str(filePath) + str(fileChoice)
	#epics.autosave.restore_pvs(saveRestoreString, debug=True)
	save_restore.restore_pvs(saveRestoreString, debug=True)


def folderSearch(path, fileExtention):
	'''Seach a folder, return the contents in a list'''
	print '...searching folder: ' + str(path)
	
	tempList = os.listdir(path)
	finalList = []
	for item in tempList:
		if item.endswith(fileExtention):
			print '...adding file: ' + str(item)
			finalList.append(item)
	
	print '...Folder Contents = ' + str(tempList)	
	print '...File List: ' + str(finalList)
	return finalList
