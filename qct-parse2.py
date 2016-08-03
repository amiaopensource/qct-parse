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
	parser.add_argument('-o','--over',dest='o',help="the threshold overage number")
	args = parser.parse_args()
	overdict = {} #init holding object for {'timestamp':'lavfi-value'} pairs
	count = 0 #init total frames counter
	with gzip.open(args.i) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): #iterparse the xml doc
			if elem.attrib['media_type'] == "video": #get just the video frames
				count = count + 1
				for t in list(elem): #elements are like lists, but you have to explicitly declare them lists to iterate, 't' in this case is <tag>
					if t.attrib['key'] == 'lavfi.signalstats.' + args.t: #grab just the attribute we want
						if int(t.attrib['value']) > int(args.o): #if the attribute is over usr set threshold
							overdict[elem.attrib['best_effort_timestamp_time']] = t.attrib['value'] #pop the timestamp, value into a dict
							#foo = raw_input("eh")
			elem.clear() #we're done with that element so let's get it outta memory
	#do some maths
	pctover = len(overdict) / float(count)
	pctstr = str(pctover)
	pctstr = pctstr[2:4] + "." + pctstr[4:]
	print "Number of frames over threshold= " + str(len(overdict))
	print "Which is " + pctstr + "% of the total # of frames"
	return
main()
#if event == 'start':
#		path.append(elem.tag)
#		if elem.tag == 'tag':
#			if elem.attrib['key'] == 'lavfi.signalstats.YMAX':
#				print path
#				#if elem.attrib['value'] >= 233:
#					#framelist.append