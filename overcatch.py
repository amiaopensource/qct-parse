#!/usr/bin/env python

#overcatch.py
#runs qct-parse 6 times:
#against each High, Med, Low profile for bars
#against each High, Med, Low profile for content
#takes input for single qctools report to process

import argparse
import subprocess
import os
import sys

parser = argparse.ArgumentParser(description="runs input QCTools Report against high, medium, and low tolerance profiles, for bars and content")
parser.add_argument('startObj',help='The QCTools Report to process',)
args = vars(parser.parse_args())

#set the profiles we want to run against the startObj
profileList = ["highTolerance","midTolerance","lowTolerance"]

#creates a log file in directory of startObj with name of [startObj]-overcatch.txt
logfile = open(os.path.join(os.path.dirname(args['startObj']),os.path.basename(args['startObj'] + "-overcatch.txt")),"a")

#do it
for profile in profileList:
	print profile
	output = subprocess.Popen(["python","qct-parse.py","-bd","-p",profile,"-i",args['startObj']],stdout=logfile,stderr=logfile)
	sys.stdout.flush()
	print output.communicate()
	output = subprocess.Popen(["python","qct-parse.py","-p",profile,"-i",args['startObj']],stdout=logfile,stderr=logfile)
	sys.stdout.flush()