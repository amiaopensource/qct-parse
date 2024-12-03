#!/usr/bin/env python
# qct-parse - changes made for python3 compatibility. WIP. 

# see this link for lxml goodness: http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

from lxml import etree  # for reading XML file (you will need to install this with pip)
import argparse         # for parsing input args
import configparser		# grip frame data values from a config txt file
import gzip             # for opening gzip file
import logging          # for logging output
import collections      # for circular buffer
import os      			# for running ffmpeg and other terminal commands
import subprocess		# not currently used
import gc				# not currently used
import math				# used for rounding up buffer half
import sys				# system stuff
import re				# can't spell parse without re fam
import operator
import time
import json
import shutil # dependency checking


# check that we have required software installed
def dependencies():
	"""
    Checks if required software dependencies are installed.

    This function checks for the presence of 'ffmpeg' and 'ffprobe' on the system.
    If either of these is not found, it prints an error message and exits the program.

    Returns:
    	None
    """
	depends = ['ffmpeg','ffprobe']
	for d in depends:
		if shutil.which(d) is None:
			print("Buddy, you gotta install " + d)
			sys.exit()
	return


# Creates timestamp for pkt_dts_time
def dts2ts(frame_pkt_dts_time):
	"""
    Converts a given pkt_dts_time to a human-readable timestamp formatted as HH:MM:SS.SSSS.

    Args:
        frame_pkt_dts_time (float or str): The pkt_dts_time value from the QCTools <frame> XML.

    Returns:
        str: A timestamp string in the format HH:MM:SS.SSSS.
    """
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


# initializes the log
def initLog(inputPath):
	"""
    Initializes a log file for the given input file.

    The log file is created with the same name as the input file but with a '.log' extension.

    Args:
        inputPath (str): The file path for the input file, used to create the log file.

    Returns:
    None
    """
	logPath = inputPath + '.log'
	logging.basicConfig(filename=logPath,level=logging.INFO,format='%(asctime)s %(message)s')
	logging.info("Started QCT-Parse")
	

# finds stuff over/under threshold
def threshFinder(inFrame,args,startObj,pkt,tag,over,thumbPath,thumbDelay,adhoc_tag):
	"""
    Evaluates whether a tag in a video frame exceeds or falls below a threshold value and logs the result.

    This function checks if a given frame's tag value is either below or above a threshold.
    It logs a warning if the value is outside the expected range and can optionally export a thumbnail.
    
    Args:
        inFrame (dict): Dictionary containing frame data.
        args (argparse.Namespace): Parsed command-line arguments.
        startObj (object): Path to the QCTools report file (.qctools.xml.gz)
        pkt (str): The key used to extract timestamps from <frame> tag in qctools.xml.gz.
        tag (str):  Tag from frame in qctools.xml.gz, checked against thresholds.
        over (float): Threshold for the tag value.
        thumbPath (str): Path to save thumbnails if they are exported.
        thumbDelay (int): Current delay counter for thumbnail exports.

    Returns:
        tuple:
            bool: indicating if threshold was met (True or False)
            int: Updated `thumbDelay` value based on whether a thumbnail was exported or not.
    
    Behavior:
        - If the tag value is below the lower threshold (for keys containing "MIN" or "LOW"), logs a warning and may export a thumbnail.
        - If the tag value is above the upper threshold, logs a warning and may export a thumbnail.
        - Thumbnail export occurs if enabled (`args.te`) and if the delay since the last export exceeds the user-defined threshold (`args.ted`).
    """
	tagValue = float(inFrame[tag])
	frame_pkt_dts_time = inFrame[pkt]
	if adhoc_tag:
		if args.o:
			comparision = operator.gt
		elif args.u:
			comparision = operator.lt
	else:
		if "MIN" in tag or "LOW" in tag:
			comparision = operator.lt
		else:
			comparision = operator.gt
	
	if comparision(float(tagValue), float(over)): # if the attribute is over usr set threshold
		timeStampString = dts2ts(frame_pkt_dts_time)
		logging.warning(tag + " is over " + str(over) + " with a value of " + str(tagValue) + " at duration " + timeStampString)
		if args.te and (thumbDelay > int(args.ted)): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
			printThumb(args,tag,startObj,thumbPath,tagValue,timeStampString)
			thumbDelay = 0
		return True, thumbDelay # return true because it was over and thumbDelay
	else:
		return False, thumbDelay # return false because it was NOT over and thumbDelay


def get_video_resolution(input_video):
    """
    Use ffprobe to get the resolution of the input video file.

    Args:
        input_video (str): Path to the input video file.

    Returns:
        (width, height) (tuple): The width and height of the video.
    """
    ffprobe_command = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 
        'stream=width,height', '-of', 'json', input_video
    ]
    
    process = subprocess.Popen(ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    
    if process.returncode != 0:
        print(f"Error getting resolution with ffprobe: {err.decode('utf-8')}")
        return None
    
    # Parse the JSON output
    video_info = json.loads(out)
    
    # Extract the width and height from the video stream info
    width = video_info['streams'][0]['width']
    height = video_info['streams'][0]['height']
    
    return width, height


# print thumbnail images of overs/unders	
def printThumb(args,tag,startObj,thumbPath,tagValue,timeStampString):
	"""
    Generates a thumbnail image from the video based on a timestamp and attribute value.

    This function uses FFmpeg to create a thumbnail image at the specified timestamp (`timeStampString`)
    from the input video file. The thumbnail is saved with a filename based on the input video's name,
    the tag name, and its value. It ensures compatibility with Windows file paths by adjusting 
    colons in the path if needed.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        tag (str): Tag name.
        startObj (str): Path to the QCTools report file (.qctools.xml.gz)
        thumbPath (str): The directory where the thumbnail image will be saved.
        tagValue (float): The value of the tag to include in the thumbnail's filename.
        timeStampString (str): The timestamp (HH:MM:SS.SSSS) at which to generate the thumbnail.

    Returns:
        None

    Behavior:
        - Constructs the input video path by removing the `.qctools.xml.gz` extension from `startObj`.
        - If the input video file exists, it generates a thumbnail using FFmpeg at the given timestamp with a hardcoded resolution of 720x486.
        - If running on Windows, adjusts the file path to account for the colon (":") in drive letters.
        - If verbose mode is enabled (`args.q` is False), prints FFmpeg's standard output and errors.
        - Exits the program if the video file is not found in the expected directory.
    """
	#### init some variables using the args list
	inputVid = startObj.replace(".qctools.xml.gz", "")
	if os.path.isfile(inputVid):
		# Get the resolution using ffprobe
		resolution = get_video_resolution(inputVid)
		if resolution:
			width, height = resolution
		else:
			# Fall back to hardcoded resolution if ffprobe fails
			width, height = 720, 486
			
		baseName = os.path.basename(startObj)
		baseName = baseName.replace(".qctools.xml.gz", "")
		outputFramePath = os.path.join(thumbPath,baseName + "." + tag + "." + str(tagValue) + "." + timeStampString + ".png")
		ffoutputFramePath = outputFramePath.replace(":",".")
		# for windows we gotta see if that first : for the drive has been replaced by a dot and put it back

		match = ''
		match = re.search(r"[A-Z]\.\/",ffoutputFramePath) # matches pattern R./ which should be R:/ on windows
		if match:
			ffoutputFramePath = ffoutputFramePath.replace(".",":",1) # replace first instance of "." in string ffoutputFramePath

		ffmpegString = (
            f'ffmpeg -ss {timeStampString} -i "{inputVid}" -vframes 1 '
            f'-s {width}x{height} -y -update 1 "{ffoutputFramePath}"'
        )
		output = subprocess.Popen(ffmpegString,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
		out,err = output.communicate()
		# Decode byte strings to handle newlines properly
		out = out.decode('utf-8')
		err = err.decode('utf-8')
		
		if args.q is False:
			print(out)
			print(err)
	else:
		print("Input video file not found. Ensure video file is in the same directory as the QCTools report.")
		exit()
	return	
	

# detect bars	
def detectBars(args,startObj,pkt,durationStart,durationEnd,framesList,buffSize,bit_depth_10):
	"""
    Detects color bars in a video by analyzing frames within a buffered window and logging the start and end times of the bars.

    This function iterates through the frames in a QCTools report, parses each frame, 
    and analyzes specific tags (YMAX, YMIN, YDIF) to detect the presence of color bars. 
    The detection checks a frame each time the buffer reaches the specified size (`buffSize`) and ends when the frame tags no longer match the expected bar values.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        startObj (str): Path to the QCTools report file (.qctools.xml.gz)
        pkt (str): Key used to identify the packet timestamp (pkt_*ts_time) in the XML frames.
        durationStart (str): The timestamp when the bars start, initially an empty string.
        durationEnd (str): The timestamp when the bars end, initially an empty string.
        framesList (list): List of dictionaries storing the parsed frame data.
        buffSize (int): The size of the frame buffer to hold frames for analysis.

    Returns:
        tuple:
            float: The timestamp (`durationStart`) when the bars were first detected.
            float: The timestamp (`durationEnd`) when the bars were last detected.
    
    Behavior:
        - Parses the input XML file frame by frame.
        - Each frame's timestamp (`pkt_*ts_time`) and key-value pairs are stored in a dictionary (`frameDict`).
        - Once the buffer reaches the specified size (`buffSize`), it checks the middle frame's attributes:
          - Color bars are detected if `YMAX > 210`, `YMIN < 10`, and `YDIF < 3.0`.
        - Logs the start and end times of the bars and stops detection once the bars end.
        - Clears the memory of parsed elements to avoid excessive memory usage during parsing.
    
    Example log outputs:
        - "Bars start at [timestamp] ([formatted timestamp])"
        - "Bars ended at [timestamp] ([formatted timestamp])"
    """
	if bit_depth_10:
		YMAX_thresh = 800
		YMIN_thresh = 10
		YDIF_thresh = 10
	else:
		YMAX_thresh = 210
		YMIN_thresh = 10
		YDIF_thresh = 3.0
	
	with gzip.open(startObj) as xml:
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": # get just the video frames
				frame_pkt_dts_time = elem.attrib[pkt] # get the timestamps for the current frame we're looking at
				frameDict = {}  # start an empty dict for the new frame
				frameDict[pkt] = frame_pkt_dts_time  # give the dict the timestamp, which we have now
				for t in list(elem):    # iterating through each attribute for each element
					keySplit = t.attrib['key'].split(".")   # split the names by dots 
					keyName = str(keySplit[-1])             # get just the last word for the key name
					frameDict[keyName] = t.attrib['value']	# add each attribute to the frame dictionary
				framesList.append(frameDict)
				middleFrame = int(round(float(len(framesList))/2))	# i hate this calculation, but it gets us the middle index of the list as an integer
				if len(framesList) == buffSize:	# wait till the buffer is full to start detecting bars
					## This is where the bars detection magic actually happens
					# Check conditions
					if (float(framesList[middleFrame]['YMAX']) > YMAX_thresh and 
						float(framesList[middleFrame]['YMIN']) < YMIN_thresh and 
						float(framesList[middleFrame]['YDIF']) < YDIF_thresh):
							if durationStart == "":
								durationStart = float(framesList[middleFrame][pkt])
								print("Bars start at " + str(framesList[middleFrame][pkt]) + " (" + dts2ts(framesList[middleFrame][pkt]) + ")")							
							durationEnd = float(framesList[middleFrame][pkt])
					else:
						if durationStart != "" and durationEnd != "" and durationEnd - durationStart > 2:
							print("Bars ended at " + str(framesList[middleFrame][pkt]) + " (" + dts2ts(framesList[middleFrame][pkt]) + ")")							
							break
			elem.clear() # we're done with that element so let's get it outta memory
	return durationStart, durationEnd


def analyzeIt(args,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList,adhoc_tag=False,frameCount=0,overallFrameFail=0):
	"""
    Analyzes video frames from the QCTools report to detect threshold exceedances for specified tags or profiles and logs frame failures.

    This function iteratively parses video frames from a QCTools report (`.qctools.xml.gz`) and checks whether the frame attributes exceed user-defined thresholds 
    (either single tags or profiles). Threshold exceedances are logged, and frames can be flagged for further analysis. Optionally, thumbnails of failing frames can be generated.

    Args:
        args (argparse.Namespace): Parsed command-line arguments, including tag thresholds and options for profile, thumbnail export, etc.
        profile (dict): A dictionary of key-value pairs of tag names and their corresponding threshold values.
        startObj (str): Path to the QCTools report file (.qctools.xml.gz)
        pkt (str): Key used to identify the pkt_*ts_time in the XML frames.
        durationStart (float): The starting time for analyzing frames (in seconds).
        durationEnd (float): The ending time for analyzing frames (in seconds). Can be `None` to process until the end.
        thumbPath (str): Path to save the thumbnail images of frames exceeding thresholds.
        thumbDelay (int): Delay counter between consecutive thumbnail generations to prevent spamming.
        framesList (list): A circular buffer to hold dictionaries of parsed frame attributes.
        frameCount (int, optional): The total number of frames analyzed (defaults to 0).
        overallFrameFail (int, optional): A count of how many frames failed threshold checks across all tags (defaults to 0).

    Returns:
        tuple: 
            - kbeyond (dict): A dictionary where each tag is associated with a count of how many times its threshold was exceeded.
            - frameCount (int): The total number of frames analyzed.
            - overallFrameFail (int): The total number of frames that exceeded thresholds across all tags.
    
    Behavior:
        - Iteratively parses the input XML file and analyzes frames after `durationStart` and before `durationEnd`.
        - Frames are stored in a circular buffer (`framesList`), and attributes (tags) are extracted into dictionaries.
        - For each frame, checks whether specified tags exceed user-defined thresholds (from `args.o`, `args.u`, or `profile`).
        - Logs threshold exceedances and updates the count of failed frames.
        - Optionally, generates thumbnails for frames that exceed thresholds, ensuring a delay between consecutive thumbnails.

    Example usage:
        - Analyzing frames using a single tag threshold: `analyzeIt(args, {}, startObj, pkt, durationStart, durationEnd, thumbPath, thumbDelay, framesList)`
        - Analyzing frames using a profile: `analyzeIt(args, profile, startObj, pkt, durationStart, durationEnd, thumbPath, thumbDelay, framesList)`
    """
	kbeyond = {} # init a dict for each key which we'll use to track how often a given key is over
	fots = ""
	for k,v in profile.items(): 
		kbeyond[k] = 0
	with gzip.open(startObj) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": 	# get just the video frames
				frameCount = frameCount + 1
				frame_pkt_dts_time = elem.attrib[pkt] 	# get the timestamps for the current frame we're looking at
				if frame_pkt_dts_time >= str(durationStart): 	# only work on frames that are after the start time
					if durationEnd:
						if float(frame_pkt_dts_time) > durationEnd:		# only work on frames that are before the end time
							print("started at " + str(durationStart) + " seconds and stopped at " + str(frame_pkt_dts_time) + " seconds (" + dts2ts(frame_pkt_dts_time) + ") or " + str(frameCount) + " frames!")
							break
					frameDict = {}  								# start an empty dict for the new frame
					frameDict[pkt] = frame_pkt_dts_time  			# make a key for the timestamp, which we have now
					for t in list(elem):    						# iterating through each attribute for each element
						keySplit = t.attrib['key'].split(".")   	# split the names by dots 
						keyName = str(keySplit[-1])             	# get just the last word for the key name
						if len(keyName) == 1:						# if it's psnr or mse, keyName is gonna be a single char
							keyName = '.'.join(keySplit[-2:])		# full attribute made by combining last 2 parts of split with a period in btw
						frameDict[keyName] = t.attrib['value']		# add each attribute to the frame dictionary
					framesList.append(frameDict)					# add this dict to our circular buffer
					if args.pr is True:	# display "timestamp: Tag Value" (654.754100: YMAX 229) to the terminal window
						print(framesList[-1][pkt] + ": " + args.t + " " + framesList[-1][args.t])
					# Now we can parse the frame data from the buffer!	
					for k,v in profile.items():
						tag = k
						over = float(v)
						# ACTUALLY DO THE THING ONCE FOR EACH TAG
						frameOver, thumbDelay = threshFinder(framesList[-1],args,startObj,pkt,tag,over,thumbPath,thumbDelay,adhoc_tag)
						if frameOver is True:
							kbeyond[k] = kbeyond[k] + 1 # note the over in the key over dict
							if not frame_pkt_dts_time in fots: # make sure that we only count each over frame once
								overallFrameFail = overallFrameFail + 1
								fots = frame_pkt_dts_time # set it again so we don't dupe
					thumbDelay = thumbDelay + 1				
			elem.clear() # we're done with that element so let's get it outta memory
	return kbeyond, frameCount, overallFrameFail


def detectBitdepth(startObj,pkt,framesList,buffSize):
	bit_depth_10 = False
	with gzip.open(startObj) as xml:
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": # get just the video frames
				frame_pkt_dts_time = elem.attrib[pkt] # get the timestamps for the current frame we're looking at
				frameDict = {}  # start an empty dict for the new frame
				frameDict[pkt] = frame_pkt_dts_time  # give the dict the timestamp, which we have now
				for t in list(elem):    # iterating through each attribute for each element
					keySplit = t.attrib['key'].split(".")   # split the names by dots 
					keyName = str(keySplit[-1])             # get just the last word for the key name
					frameDict[keyName] = t.attrib['value']	# add each attribute to the frame dictionary
				framesList.append(frameDict)
				middleFrame = int(round(float(len(framesList))/2))	# i hate this calculation, but it gets us the middle index of the list as an integer
				if len(framesList) == buffSize:	# wait till the buffer is full to start detecting bars
					## This is where the bars detection magic actually happens
					bufferRange = list(range(0, buffSize))
					if float(framesList[middleFrame]['YMAX']) > 250:
						bit_depth_10 = True
						break
			elem.clear() # we're done with that element so let's get it outta memory

	return bit_depth_10


def evalBars(startObj,pkt,durationStart,durationEnd,framesList,buffSize):
	# Define the keys for which you want to calculate the average
	keys_to_check = ['YMAX', 'YMIN', 'UMIN', 'UMAX', 'VMIN', 'VMAX', 'SATMAX', 'SATMIN']
	# Initialize a dictionary to store the highest values for each key
	maxBarsDict = {}
	# adds the list keys_to_check as keys to a dictionary
	for key_being_checked in keys_to_check:
		# assign 'dummy' threshold to be overwritten
		if "MAX" in key_being_checked:
			maxBarsDict[key_being_checked] = 0
		elif "MIN" in key_being_checked:
			maxBarsDict[key_being_checked] = 1023
	
	with gzip.open(startObj) as xml:
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": # get just the video frames
				frame_pkt_dts_time = elem.attrib[pkt] # get the timestamps for the current frame we're looking at
				if frame_pkt_dts_time >= str(durationStart): 	# only work on frames that are after the start time   # only work on frames that are after the start time
					if float(frame_pkt_dts_time) > durationEnd:        # only work on frames that are before the end time
						break
					frameDict = {}  # start an empty dict for the new frame
					frameDict[pkt] = frame_pkt_dts_time  # give the dict the timestamp, which we have now
					for t in list(elem):    # iterating through each attribute for each element
						keySplit = t.attrib['key'].split(".")   # split the names by dots 
						keyName = str(keySplit[-1])             # get just the last word for the key name
						frameDict[keyName] = t.attrib['value']	# add each attribute to the frame dictionary
					framesList.append(frameDict)
					if len(framesList) == buffSize:	# wait till the buffer is full to start detecting bars
						## This is where the bars detection magic actually happens
						for colorbar_key in keys_to_check:
							if colorbar_key in frameDict:
								if "MAX" in colorbar_key:
									# Convert the value to float and compare it with the current highest value
									value = float(frameDict[colorbar_key])
									if value > maxBarsDict[colorbar_key]:
										maxBarsDict[colorbar_key] = value
								elif "MIN" in colorbar_key:
									# Convert the value to float and compare it with the current highest value
									value = float(frameDict[colorbar_key])
									if value < maxBarsDict[colorbar_key]:
										maxBarsDict[colorbar_key] = value
								# Convert highest values to integer
								maxBarsDict = {colorbar_key: int(value) for colorbar_key, value in maxBarsDict.items()}
							
		return maxBarsDict
	

def extract_report_mkv(startObj):
	
	report_file_output = startObj.replace(".qctools.mkv", ".qctools.xml.gz")
	if os.path.isfile(report_file_output):
		while True:
			user_input = input(f"The file {os.path.basename(report_file_output)} already exists. \nExtract xml.gz from {os.path.basename(startObj)} and overwrite existing file? \n(y/n):\n")
			if user_input.lower() in ["yes", "y"]:
				os.remove(report_file_output)
				# Run ffmpeg command to extract xml.gz report
				full_command = [
					'ffmpeg', 
					'-hide_banner', 
					'-loglevel', 'panic', 
					'-dump_attachment:t:0', report_file_output, 
					'-i', startObj
				]
				print(f'Extracting qctools.xml.gz report from {os.path.basename(startObj)}\n')
				print(f'Running command: {" ".join(full_command)}\n')
				subprocess.run(full_command)
				break
			elif user_input.lower() in ["no", "n"]:
				print('Processing existing qctools report, not extracting file\n')
				break
			else:
				print("Invalid input. Please enter yes/no.\n")
	else:
		# Run ffmpeg command to extract xml.gz report
		full_command = [
			'ffmpeg', 
			'-hide_banner', 
			'-loglevel', 'panic', 
			'-dump_attachment:t:0', report_file_output, 
			'-i', startObj
		]
		print(f'Extracting qctools.xml.gz report from {os.path.basename(startObj)}\n')
		print(f'Running command: {" ".join(full_command)}\n')
		subprocess.run(full_command)

	if os.path.isfile(report_file_output):
		startObj = report_file_output
	else:
		print(f'Unable to extract XML from QCTools mkv report file\n')
		startObj = None
		exit()
	
	return startObj


def print_peak_colorbars(maxBarsDict):
	# ASCI formatting
	BOLD = "\033[1m"
	RESET = "\033[0m"

	print("\nReporting frames outside of these thresholds:")

	# Create two lists for even and odd indices
	tags = list(maxBarsDict.keys())
	values = list(maxBarsDict.values())

	# Print even-indexed tags and values on the first line
	for i in range(0, len(tags), 2):
		print(f"{BOLD}{tags[i]:<6}{RESET} {values[i]:<5}", end="   ")
	print()  # Move to the next line

	# Print odd-indexed tags and values on the second line
	for i in range(1, len(tags), 2):
		print(f"{BOLD}{tags[i]:<6}{RESET} {values[i]:<5}", end="   ")
	print()  # Move to the next line


# Print results from analyzeIt	
def printresults(kbeyond, frameCount, overallFrameFail):
	"""
	Prints the analysis results of frame data, including counts of frames exceeding thresholds 
	for various tags and the percentage of total frames that are affected.

	Args:
		kbeyond (dict): A dictionary where keys are tag names and values are the counts of frames 
						that exceed the threshold for each tag.
		frameCount (int): The total number of frames analyzed.
		overallFrameFail (int): The number of frames where at least one tag exceeds its threshold.

	Prints:
		- The total number of frames analyzed.
		- A breakdown of frame counts for each tag in `kbeyond` and the corresponding percentage 
			of the total frames that exceeded the tag's threshold.
		- The overall count and percentage of frames that failed at least one threshold.

	Notes:
		- If `frameCount` is zero, it prints "TotalFrames: 0" and returns early.
		- Percentages are formatted as whole numbers (e.g., "100"), two decimal places 
			(e.g., "12.34"), or "<0.01" for values less than 0.01%.
	"""
	# Define ANSI escape codes for color and formatting
	BOLD = "\033[1m"
	UNDERLINE = "\033[4m"
	RESET = "\033[0m"

	RED = "\033[91m"
	YELLOW = "\033[93m"
	GREEN = "\033[92m"

	def format_percentage(value):
		percent = value * 100
		if percent == 100:
			return "100"
		elif percent == 0:
			return "0"
		elif percent < 0.01:
			return "<0.01"
		else:
			return f"{percent:.2f}"

	def color_percentage(value):
		percent = value * 100
		if percent > 10:
			return RED
		elif percent > 1:
			return YELLOW
		else:
			return GREEN

	if frameCount == 0:
		print(f"{UNDERLINE}TotalFrames:{RESET}\t0")
		return

	print(f"\n{UNDERLINE}TotalFrames{RESET}:\t{frameCount}\n")
	print(f"{UNDERLINE}By Tag{RESET}:\n")

	for tag, count in kbeyond.items():
		percent = count / frameCount
		percent_over_string = format_percentage(percent)
		color = color_percentage(percent)
		print(f"{BOLD}{tag}{RESET}:\t{count}\t{color}{percent_over_string}{RESET}\t% of the total # of frames\n")

	print(f"{BOLD}Overall:{RESET}\n")
	overall_percent = overallFrameFail / frameCount
	percent_overall_string = format_percentage(overall_percent)
	color = color_percentage(overall_percent)
	print(f"Frames With At Least One Fail:\t{overallFrameFail}\t{color}{percent_overall_string}{RESET}\t% of the total # of frames\n")
	print(f"{BOLD}**************************{RESET}\n")

	
def main():
	"""
    Main function that parses QCTools XML files, applies analysis, and optionally exports thumbnails.

    This function handles command-line arguments to process a QCTools report, extract frame data from the XML, 
    apply threshold analysis for broadcast values, optionally detect color bars, and export analysis results to 
    the console or thumbnails.

    Command-line Arguments:
        -i, --input (str): Path to the input QCTools XML.gz file.
        -t, --tagname (str): Tag name to analyze, e.g., SATMAX.
        -o, --over (float): Overage threshold for the tag specified.
        -u, --under (float): Under threshold for the tag specified.
        -p, --profile (str): Profile or template name from the qct-parse_config.txt file, e.g., 'default'.
        -buff, --buffSize (int): Circular buffer size. Defaults to 11, ensures odd number.
        -te, --thumbExport: Export thumbnails if flag is set.
        -ted, --thumbExportDelay (int): Minimum number of frames between exported thumbnails.
        -tep, --thumbExportPath (str): Path to export thumbnails, defaults to input basename if not provided.
        -ds, --durationStart (float): Start time in seconds for analysis.
        -de, --durationEnd (float): End time in seconds for analysis.
        -bd, --barsDetection: Flag to enable color bars detection.
        -pr, --print: Flag to print frame data to the console.
        -q, --quiet: Hide ffmpeg output if flag is set.

    Workflow:
        1. Parse command-line arguments.
        2. Optionally load reference threshold values from a profile in `qct-parse_config.txt`.
        3. Initialize buffers, frame counters, and paths for thumbnail export.
        4. Check for `pkt_dts_time` or `pkt_pts_time` in the QCTools XML file.
        5. Set the analysis duration start and end times.
        6. Perform bars detection if enabled, otherwise proceed with general analysis.
        7. Call the `analyzeIt` function to perform frame-by-frame analysis and calculate exceedances.
        8. Print results using `printresults` if applicable.
        9. Handle errors or invalid input (e.g., missing thumbnail export flag but specifying a path).

    Example usage:
        python qct-parse.py -i sample.qctools.xml.gz -t SATMAX -o 5.0 -u -5.0 -te

    Returns:
        None: The function processes the XML file, performs analysis, and optionally exports thumbnails and prints results to the console.
    """
	#### init the stuff from the cli ########
	parser = argparse.ArgumentParser(description="parses QCTools XML files for frames beyond broadcast values")
	parser.add_argument('-i','--input',dest='i', help="the path to the input qctools.xml.gz file")
	parser.add_argument('-t','--tagname',dest='t', help="the tag name you want to test, e.g. SATMAX")
	parser.add_argument('-o','--over',dest='o', help="the threshold overage number")
	parser.add_argument('-u','--under',dest='u', help="the threshold under number")
	parser.add_argument('-p','--profile', dest='p', nargs='*', default=None, help="use values from your qct-parse-config.txt file, provide profile/ template name, e.g. 'default'")
	parser.add_argument('-buff','--buffSize',dest='buff',default=11, help="Size of the circular buffer. if user enters an even number it'll default to the next largest number to make it odd (default size 11)")
	parser.add_argument('-te','--thumbExport',dest='te',action='store_true',default=False, help="export thumbnail")
	parser.add_argument('-ted','--thumbExportDelay',dest='ted',default=9000, help="minimum frames between exported thumbs")
	parser.add_argument('-tep','--thumbExportPath',dest='tep',default='', help="Path to thumb export. if omitted, it uses the input basename")
	parser.add_argument('-ds','--durationStart',dest='ds',default=0, help="the duration in seconds to start analysis")
	parser.add_argument('-de','--durationEnd',dest='de',default=99999999, help="the duration in seconds to stop analysis")
	parser.add_argument('-bd','--barsDetection',dest='bd',action ='store_true',default=False, help="turns Bar Detection on and off")
	parser.add_argument('-be','--barsEvaluation',dest='be',action ='store_true',default=False, help="turns Color Bar Evaluation on and off")
	parser.add_argument('-pr','--print',dest='pr',action='store_true',default=False, help="print over/under frame data to console window")
	parser.add_argument('-q','--quiet',dest='q',action='store_true',default=False, help="hide ffmpeg output from console window")
	args = parser.parse_args()
	
	## Validate required arguments
	if not args.i:
		parser.error("the following arguments are required: -i/--input [path to QCTools report]")
	if args.o and args.u:
		parser.error("Both the -o and -u options were used. Cannot set threshold for both over and under, only one at a time.")
	
	##### Initialize variables and buffers ######
	startObj = args.i.replace("\\","/")
	extension = os.path.splitext(startObj)[1]
	# If qctools report is in an MKV attachment, extract .qctools.xml.gz report 
	if extension.lower().endswith('mkv'):
		startObj = extract_report_mkv(startObj)
	buffSize = int(args.buff)   # cast the input buffer as an integer
	if buffSize%2 == 0:
		buffSize = buffSize + 1
	initLog(startObj)	# initialize the log
	overcount = 0	# init count of overs
	undercount = 0	# init count of unders
	count = 0		# init total frames counter
	framesList = collections.deque(maxlen=buffSize) # init framesList 
	thumbDelay = int(args.ted)	# get a seconds number for the delay in the original file btw exporting tags
	parentDir = os.path.dirname(startObj)
	baseName = os.path.basename(startObj)
	baseName = baseName.replace(".qctools.xml.gz", "")
	durationStart = args.ds
	durationEnd = args.de

	# we gotta find out if the qctools report has pkt_dts_time or pkt_pts_time ugh
	with gzip.open(startObj) as xml:    
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'):  # iterparse the xml doc
			if elem.attrib['media_type'] == "video":  # get just the video frames
				# we gotta find out if the qctools report has pkt_dts_time or pkt_pts_time ugh
				match = re.search(r"pkt_.ts_time", etree.tostring(elem).decode('utf-8'))
				if match:
					pkt = match.group()
					break

	###### Initialize values from the Config Parser
	# Determine if video values are 10 bit depth 
	bit_depth_10 = detectBitdepth(startObj,pkt,framesList,buffSize)
	# init a dictionary where we'll store reference values from our config file
	profile = {} 
	# init a list of every tag available in a QCTools Report
	tagList = ["YMIN","YLOW","YAVG","YHIGH","YMAX","UMIN","ULOW","UAVG","UHIGH","UMAX","VMIN","VLOW","VAVG","VHIGH","VMAX","SATMIN","SATLOW","SATAVG","SATHIGH","SATMAX","HUEMED","HUEAVG","YDIF","UDIF","VDIF","TOUT","VREP","BRNG","mse_y","mse_u","mse_v","mse_avg","psnr_y","psnr_u","psnr_v","psnr_avg"]

	# set the start and end duration times
	if args.bd:
		durationStart = ""				# if bar detection is turned on then we have to calculate this
		durationEnd = ""				# if bar detection is turned on then we have to calculate this
	elif args.ds:
		durationStart = float(args.ds) 	# The duration at which we start analyzing the file if no bar detection is selected
	elif not args.de == 99999999:
		durationEnd = float(args.de) 	# The duration at which we stop analyzing the file if no bar detection is selected
	
	
	# set the path for the thumbnail export	
	if args.tep and not args.te:
		print("Buddy, you specified a thumbnail export path without specifying that you wanted to export the thumbnails. Please either add '-te' to your cli call or delete '-tep [path]'")
		exit()
	
	if args.tep: # if user supplied thumbExportPath, use that
		thumbPath = str(args.tep)
	else:
		if args.t: # if they supplied a single tag
			if args.o: # if the supplied tag is looking for a threshold Over
				thumbPath = os.path.join(parentDir, str(args.t) + "." + str(args.o))
			elif args.u: # if the supplied tag was looking for a threshold Under
				thumbPath = os.path.join(parentDir, str(args.t) + "." + str(args.u))
		else: # if they're using a profile, put all thumbs in 1 dir
			thumbPath = os.path.join(parentDir, "ThumbExports")
	
	if args.te: # make the thumb export path if it doesn't already exist
		if not os.path.exists(thumbPath):
			os.makedirs(thumbPath)
	
	
	######## Iterate Through the XML for Bars detection ########
	if args.bd:
		print(f"\nStarting Bars Detection on {baseName}\n")
		durationStart, durationEnd = detectBars(args,startObj,pkt,durationStart,durationEnd,framesList,buffSize,bit_depth_10)
		if args.be and durationStart != "" and durationEnd != "":
			maxBarsDict = evalBars(startObj,pkt,durationStart,durationEnd,framesList,buffSize)
			if maxBarsDict is None:
				print("\nSomething went wrong - cannot run colorbars evaluation")
			else:
				print("\nNow comparing peak values of color bars to the rest of the video.")
				print_peak_colorbars(maxBarsDict)
				# Reset start and stop time to eval the whole video (color bars won't be flagged because we already have their max values)
				durationStart = 0
				durationEnd = 99999999
				profile = maxBarsDict
				kbeyond, frameCount, overallFrameFail = analyzeIt(args,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList,adhoc_tag=False)
				printresults(kbeyond,frameCount,overallFrameFail)
		else:
			durationStart = ""
			durationEnd = ""
	
	if args.p is not None:
		# create list of profiles
		list_of_templates = args.p
		# setup configparser
		config = configparser.RawConfigParser(allow_no_value=True)
		dn, fn = os.path.split(os.path.abspath(__file__)) # grip the dir where ~this script~ is located, also where config.txt should be located
		# assign config based on bit depth of tag values 
		if bit_depth_10:
			config.read(os.path.join(dn,"qct-parse_10bit_config.txt")) # read in the config file
		else:
			config.read(os.path.join(dn,"qct-parse_8bit_config.txt")) # read in the config file
		for template in list_of_templates:
			# Check if the template is a valid section in the config
			if not config.has_section(template):
				print(f"Profile '{template}' does not match any section in the config.")
				continue  # Skip to the next template if section doesn't exist
			for t in tagList: 			# loop thru every tag available and 
				try: 					# see if it's in the config section
					profile[t.replace("_",".")] = config.get(template,t) # if it is, replace _ necessary for config file with . which xml attributes use, assign the value in config
				except: # if no config tag exists, do nothing so we can move faster
					pass

			######## Iterate Through the XML for General Analysis ########
			print(f"\nStarting Analysis on {baseName} using assigned profile {template}\n")
			kbeyond, frameCount, overallFrameFail = analyzeIt(args,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList,adhoc_tag=False)
			printresults(kbeyond,frameCount,overallFrameFail)
	
	if args.t and args.o or args.u: 
		profile = {}
		tag = args.t
		if args.o:
			over = float(args.o)
		if args.u:
			over = float(args.u)
		profile[tag] = over
		print(f"\nStarting Analysis on {baseName} using user specified tag {tag} w/ threshold {over}\n")
		kbeyond, frameCount, overallFrameFail = analyzeIt(args,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList,adhoc_tag = True)
		printresults(kbeyond,frameCount,overallFrameFail)
	
	print(f"\nFinished Processing File: {baseName}.qctools.xml.gz\n")
	
	return

if __name__ == '__main__':
	dependencies()
	main()