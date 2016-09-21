#qct-parse3.2 -> fixed bugs in 3.1

#see this link for lxml goodness: http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

from lxml import etree  #for reading XML file (you will need to install this with pip)
import argparse         #for parsing input args (Which there are a lot of now lol)
import gzip             #for opening gzip file
import logging          #for logging output
import collections      #for circular buffer
import os      			#for running ffmpeg and other terminal commands
import subprocess		#not currently used
import gc				#not currently used
import math				#used for rounding up buffer half

#Creates timestamp for pkt_dts_time
def dts2ts(frame_pkt_dts_time):
    
    seconds = float(frame_pkt_dts_time)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    if hours < 10:
        hours = "0" + str(int(hours))
    else:
        hours = str(int(hours))
        
    if minutes < 10:
        minutes = "0" + str(int(minutes))
    else:
        minutes = str(int(minutes))
    
    secondsStr = str(round(seconds,4))
    
    if int(seconds) < 10:
        secondsStr = "0" + secondsStr
    else:
        seconds = str(minutes)
    while len(secondsStr) < 7:
        secondsStr = secondsStr + "0"
   
    timeStampString = hours + ":" + minutes + ":" + secondsStr
    return timeStampString

#Initializes the log
def initLog(inputPath):
	logPath = inputPath + '.log'
	logging.basicConfig(filename=logPath,level=logging.INFO,format='%(asctime)s %(message)s')
	logging.info("Started QCT-Parse")
	
#Finds Overs
def overFinder(inFrame, args, thumbPath, thumbDelay):
	####init some variables using the args list
	inputVid = args.i.replace(".qctools.xml.gz", "")
	baseName = os.path.basename(args.i)
	baseName = baseName.replace(".qctools.xml.gz", "")
	tagValue = int(inFrame[args.t])
	
	####czech for overs
	frame_pkt_dts_time = inFrame['pkt_dts_time']
	if tagValue > int(args.o): #if the attribute is over usr set threshold
		timeStampString = dts2ts(frame_pkt_dts_time)
		logging.warning(args.t + " is over " + args.o + " with a value of " + str(tagValue) + " at duration " + timeStampString)
		outputFramePath = thumbPath + baseName + "." + args.t + "." + str(tagValue) + "." + timeStampString + ".png"
		if args.te and (thumbDelay > int(args.ted)): #if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
			ffmpegString = "ffmpeg -i '" + inputVid + "' -ss " + timeStampString + " -vframes 1 -y '" + outputFramePath.replace(":",".") + "' >/dev/null 2>&1"
		#	print ffmpegString
		#	os.system(ffmpegString)
			thumbDelay = 0 	
		return 1, thumbDelay #return 1 because it was over and thumbDelay
	return 0, thumbDelay #return 1 because it was NOT over and thumbDelay
	
def main():
	####init the stuff from the cli########
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input',dest='i',help="the path to the input qctools.xml.gz file")
	parser.add_argument('-t','--tagname',dest='t',help="the tag name you want to test, e.g. SATMAX")
	parser.add_argument('-o','--over',dest='o',help="the threshold overage number")
	parser.add_argument('-buff','--buffSize',dest='buff',default=11, help="Size of the circular buffer. if user enters an even number it'll default to the next largest number to make it odd (default size 11)")
	parser.add_argument('-te','--thumbExport',dest='te',default=0, help="0 for no thumb export, 1 for thumb export")
	parser.add_argument('-ted','--thumbExportDelay',dest='ted',default=9000, help="minimum frames between exported thumbs")
	parser.add_argument('-tep','--thumbExportPath',dest='tep',default=0, help="Path to thumb export. if ommitted, it uses the input basename")
	parser.add_argument('-ds','--durationStart',dest='ds',default=0, help="the duration in seconds to start analysis")
	parser.add_argument('-de','--durationEnd',dest='de',default=9999999999, help="the duration in seconds to stop analysis")
	parser.add_argument('-bd','--barsDetection',dest='bd',default=0, help="turns Bar Detection on and off")

	args = parser.parse_args()	
	buffSize = int(args.buff)   #cast the input buffer as an integer
	if buffSize%2 == 0:
		buffSize = buffSize + 1
	#######################################
	
	######Initialize some other stuff######
	initLog(args.i) #initialize the log
	overcount = 0 # init count of overs
	undercount = 0 # init count of unders
	count = 0 #init total frames counter
	framesList = collections.deque(maxlen=buffSize) # init holding object for holding all frame data in a circular buffer. 
	bdFramesList = collections.deque(maxlen=buffSize) # init holding object for holding all frame data in a circular buffer. 
	thumbDelay = int(args.ted)	
	parentDir = os.path.dirname(args.i)
	baseName = os.path.basename(args.i)
	baseName = baseName.replace(".qctools.xml.gz", "")
	if args.bd:
		durationStart = ""				#if bar detection is turned on then we have to calculate this
		durationEnd = ""				#if bar detection is turned on then we have to calculate this
	else:
		durationStart = float(args.ds) 	#The duration at which we start analyzing the file if no bar detection is selected
		durationEnd = float(args.de) 	#The duration at which we stop analyzing the file if no bar detection is selected
	if args.tep:
	    if args.tep[-1] != "/":
	        thumbPath = str(args.tep) + "/"
	    else:
	        thumbPath = str(args.tep)
	else:
	    thumbPath = parentDir + "/" + str(args.t) + "." + str(args.o) + "/"
	if args.te:
		try:
			os.makedirs(thumbPath)
		except:
			print "Thumbs Directory Already Exists!"
    #######################################	
	
	########Iterate Through the XML for Bars detection########
	if args.bd:
		print "Starting Bars Detection on " + baseName
		with gzip.open(args.i) as xml:	
			for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): #iterparse the xml doc
				if elem.attrib['media_type'] == "video": #get just the video frames
					frame_pkt_dts_time = elem.attrib['pkt_dts_time'] #get the timestamps for the current frame we're looking at
					frameDict = {}  #start an empty dict for the new frame
					frameDict['pkt_dts_time'] = frame_pkt_dts_time  #give the dict the timestamp, which we have now
					for t in list(elem):    #iterating through each attribute for each element
						keySplit = t.attrib['key'].split(".")   #split the names by dots 
						keyName = str(keySplit[-1])             #get just the last word for the key name
						frameDict[keyName] = t.attrib['value']	#add each attribute to the frame dictionary
					framesList.append(frameDict)
					middleFrame = int(round(float(len(framesList))/2))	#i hate this calculation, but it gets us the middle index of the list as an integer
					if len(framesList) == buffSize:	#wait till the buffer is full to start detecting bars
						##This is where the bars detection magic actually happens
						bufferRange = range(0, buffSize)
						if int(framesList[middleFrame]['YMAX']) > 210 and int(framesList[middleFrame]['YMIN']) < 10 and float(framesList[middleFrame]['YDIF']) < 3.0:
							if durationStart == "":
								durationStart = float(framesList[middleFrame]['pkt_dts_time'])
								print "Bars start at " + str(framesList[middleFrame]['pkt_dts_time']) + " (" + dts2ts(framesList[middleFrame]['pkt_dts_time']) + ")"							
							durationEnd = float(framesList[middleFrame]['pkt_dts_time'])
						else:
							print "Bars ended at " + str(framesList[middleFrame]['pkt_dts_time']) + " (" + dts2ts(framesList[middleFrame]['pkt_dts_time']) + ")"							
							break
				elem.clear() #we're done with that element so let's get it outta memory
	#######################################
	
	
	
	########Iterate Through the XML for General Analysis########
	print "Starting Analysis on " + baseName
	with gzip.open(args.i) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): #iterparse the xml doc
			if elem.attrib['media_type'] == "video": #get just the video frames
				frame_pkt_dts_time = elem.attrib['pkt_dts_time'] #get the timestamps for the current frame we're looking at
				if float(frame_pkt_dts_time) >= durationStart:
					if float(frame_pkt_dts_time) > durationEnd:
						print "started at " + str(durationStart) + " seconds and stopped at " + str(frame_pkt_dts_time) + " seconds (" + dts2ts(frame_pkt_dts_time) + ") or " + str(count) + " frames!"
						break
					frameDict = {}  #start an empty dict for the new frame
					frameDict['pkt_dts_time'] = frame_pkt_dts_time  #give the dict the timestamp, which we have now
					for t in list(elem):    #iterating through each attribute for each element
						keySplit = t.attrib['key'].split(".")   #split the names by dots 
						keyName = str(keySplit[-1])             #get just the last word for the key name
						frameDict[keyName] = t.attrib['value']	#add each attribute to the frame dictionary
					framesList.append(frameDict)
				
					#The following line will display "timestamp: Tag Value" (654.754100: YMAX 229) to the terminal window. commented out, but it's a nice examples
					#print framesList[-1]['pkt_dts_time'] + ": " + args.t + " " + framesList[-1][args.t]
				
				
					#Now we can parse the frame data from the buffer! we should probably make individual functions out of each of these.
							
					#use the overFinder() function to find overs
					frameOver = 0
					if args.o:
						frameOver, thumbDelay = overFinder(framesList[-1], args, thumbPath, thumbDelay)
						if frameOver == 1:
							overcount = overcount + 1
					count = count + 1	
					thumbDelay = thumbDelay + 1					
			elem.clear() #we're done with that element so let's get it outta memory
	#######################################	
	
	
	#do some maths for the printout
	print "Finished Processing File: " + baseName + ".qctools.xml.gz"


	if args.o:
		if count == 0:
			percentOverString = "0"
		else:
			percentOver = float(overcount) / float(count)
			if percentOver == 1:
				percentOverString = "100"
			else:
				percentOverString = str(percentOver)
				percentOverString = percentOverString[2:4] + "." + percentOverString[4:]
		print "Number of frames over threshold= " + str(overcount)
		print "Which is " + percentOverString + "% of the total # of frames"
		print "##############################################################"
		print ""
		
	return
main()

