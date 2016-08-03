#qct-parse2
import xml.etree.ElementTree as etree

xml = "S:/avlab/qct-parse/cpb-aacip-507-9p2w37mc70.mxf.qctools.xml"

for event, elem in etree.iterparse(xml, events=('start','end','start-ns','end-ns')):
	print event, elem
	foo = raw_input("eh")