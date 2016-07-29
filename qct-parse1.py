import xmltodict
import argparse
import gzip

def main():
	#init the stuff from the cli
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input',dest='i',help="the path to the input qctools.xml.gz file")
	parser.add_argument('-t','--tagname',dest='t',help="the tag name you want to test, e.g. SATMAX")
	parser.add_argument('-o','--over',dest='o',help="the threshold overage number")
	args = parser.parse_args()
	overthresh = {}
	count = 0 #initialize a var for the number of frames total
	with gzip.open(args.i) as fd: #use the gzip lib to open the file
		doc = xmltodict.parse(fd.read()) #assign it to a dict with xmltodict lib
		print 'done loading'
		frame = doc['ffprobe:ffprobe']['frames']['frame'] #drill into hierarchy to get to just the frames
		for f in frame: #f is actually a single frame, frame is the parent of all the frames... idk man
			if f['@media_type'] == "video": #weed out audio frames
				count = count + 1 #this is a video frame so increase the count
				stats = f['tag'] #qctools reports have all the stats labelled with "tag", is is an OrderedDict at this point btw
				for stat in stats: #for each tag in the OrderedDict of tags
					if stat['@key'] == "lavfi.signalstats." + args.t: #this is how you access a single stat in a frame
						if int(stat['@value']) >= int(args.o): #if attribute "value" is greater than the threshold we specify
							key = f['@best_effort_timestamp_time'] #assign a var to the timestamp
							overthresh[key] = stat['@value'] #append it to dict of {'timestamp' : 'overageNumber'} values
		#do some maths
		pctover = len(overthresh) / float(count)
		pctstr = str(pctover)
		pctstr = pctstr[2:4] + "." + pctstr[4:]
		print "Number of frames over threshold= " + str(len(overthresh))
		print "Which is " + pctstr + "% of the total # of frames"
	
	return

main()