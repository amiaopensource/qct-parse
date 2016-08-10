#qct-parse2
#see this link for lxml goodness: http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

from lxml import etree
import argparse
import gzip

def main():
	#init the stuff from the cli
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input',dest='i',help="the path to the input qctools.xml.gz file")
	parser.add_argument('-t','--tagname',dest='t',help="the tag name you want to test, e.g. SATMAX")
	parser.add_argument('-o','--over',dest='o',help="value for the upper threshold")
	parser.add_argument('-u','--under',dest='u',help="value for the lower threshold")
	args = parser.parse_args()
	overdict = {} #init holding object for {'timestamp':'lavfi-value'} pairs
	underdict = {} #init holding object for {'timestamp':'lavfi-value'} pairs
	count = 0 #init total frames counter
	with gzip.open(args.i) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): #iterparse the xml doc
			if elem.attrib['media_type'] == "video": #get just the video frames
				count = count + 1
				for t in list(elem): #elements are like lists, but you have to explicitly declare them lists to iterate, 't' in this case is <tag>
					if t.attrib['key'] == 'lavfi.signalstats.' + args.t: #grab just the attribute we want
						if float(t.attrib['value']) > float(args.o): #if the attribute is over usr set threshold
							overdict[elem.attrib['best_effort_timestamp_time']] = t.attrib['value'] #pop the timestamp, value into a dict
						if float(t.attrib['value']) < float(args.u):
							underdict[elem.attrib['best_effort_timestamp_time']] = t.attrib['value']
							#foo = raw_input("eh")
			elem.clear() #we're done with that element so let's get it outta memory
	#do some maths for the printout
	pctover = len(overdict) / float(count)
	pctostr = str(pctover)
	pctostr = pctostr[2:4] + "." + pctostr[4:]
	pctunder = len(underdict) / float(count)
	pctustr = str(pctunder)
	pctustr = pctustr[2:4] + "." + pctustr[4:]
	print "Number of frames over threshold= " + str(len(overdict))
	print "Which is " + pctostr + "% of the total # of frames"
	print "Number of frames under threshold= " + str(len(underdict))
	print "Which is " + pctustr + "% of the total # of frames"
	return
main()
