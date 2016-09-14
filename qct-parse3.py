#qct-parse3.1
#see this link for lxml goodness: http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

from lxml import etree  #for reading XML file (you will need to install this with pip)
import argparse         #for parsing input args (Which there are a lot of now lol)
import gzip             #for opening gzip file
import logging          #for logging output
import collections      #for circular buffer
import os       		#for path stuff mostly
import subprocess		#for calling utils thru cli


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
	
def main():
	####init the stuff from the cli########
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input',dest='i',help="the path to the input qctools.xml.gz file")
	parser.add_argument('-t','--tagname',dest='t',help="the tag name you want to test, e.g. SATMAX")
	parser.add_argument('-o','--over',dest='o',help="the threshold overage number")
	parser.add_argument('-buff','--buffSize',dest='buff',default=10, help="Size, in frames, of the circular buffer, defaults to 10")
	parser.add_argument('-te','--thumbExport',dest='te',action="store_true",default=False, help="export thumbnail imgs for over/under frames, default is no")
	parser.add_argument('-ted','--thumbExportDelay',dest='ted',default=9000, help="minimum frames between exported thumbs, default is 9000")
	parser.add_argument('-tep','--thumbExportPath',dest='tep',default=0, help="Path to thumb export, defaults to input qctools report path")
	args = parser.parse_args()	
	   #cast the input buffer as an integer

	
	######Initialize some other stuff######
	buffSize = int(args.buff)
	initLog(args.i) #initialize the log
	overdict = {} #init holding object for {'timestamp':'lavfi-value'} pairs
	count = 0 #init total frames counter
	framesList = collections.deque(maxlen=buffSize) # init holding object for holding all frame data in a circular buffer. 
	inputVid = args.i.replace(".qctools.xml.gz", "")
	thumbDelay = args.ted
	baseName = os.path.basename(args.i)
	baseName = baseName.replace(".qctools.xml.gz", "")
	parentDir = os.path.dirname(args.i)
	thumbsExportDir
	
	#init the path for thumbnail exports
	if args.tep:
	    if not os.path.exists(args.tep):
			os.makedirs(args.tep)
	else:
	    thumbsPath = os.path.join(parentDir, + str(args.t) + "." + str(args.o))
	
	########Iterate Through the XML########
	with gzip.open(args.i) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): #iterparse the xml doc
			if elem.attrib['media_type'] == "video": #get just the video frames
				count = count + 1
				frame_pkt_dts_time = elem.attrib['pkt_dts_time'] #get the timestamps for the current frame we're looking at
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
				
				tagValue = int(framesList[-1][args.t])
				
				if tagValue > int(args.o): #if the attribute is over usr set threshold
					
					timeStampString = dts2ts(frame_pkt_dts_time)
					
					logging.warning(args.t + " is over " + args.o + " with a value of " + str(tagValue) + " at duration " + timeStampString)
					outputFramePath = thumbsPath + baseName + "." + args.t + "." + str(tagValue) + "." + timeStampString + ".png"
					if args.te and (thumbDelay > args.ted): #if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
					    ffmpegString = "ffmpeg -i '" + inputVid + "' -ss " + timeStampString + " -vframes 1 -y '" + outputFramePath.replace(":",".") + "' >/dev/null 2>&1"
					    print ffmpegString
					    os.system(ffmpegString)
					    thumbDelay = 0 
			thumbDelay = thumbDelay + 1					
			elem.clear() #we're done with that element so let's get it outta memory

	#######################################	
	
	
	#do some maths for the printout

	pctover = len(overdict) / float(count)
	pctstr = str(pctover)
	pctstr = pctstr[2:4] + "." + pctstr[4:]
	filePath = args.i
	filePathSplit = filePath.split('/')
	fileName = filePathSplit[-1]
	print "Finished Processing File: " + str(fileName)
	print "Number of frames over threshold= " + str(len(overdict))
	print "Which is " + pctstr + "% of the total # of frames"
	return
main()

