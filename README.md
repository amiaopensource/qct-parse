scripts for automating QCTools actions

qct-parse.py | find frames that are beyond thresholds for saturation, luma, etc

makeqctoolsreport.py | make a qctools.xml.gz report for input video file

#qct-parse.py

##arguments
  -h, --help                | show this help message and exit

  -i, --input            | the path to the input qctools.xml.gz file
  
  -t, --tagname         | the tag name you want to test, e.g. SATMAX
  
  -o, --over             | the threshold overage number
  
  -u, --under             | the threshold under number
  
  -p, --profile         | compare frame data aginst tag values from config.txt file, us "-p default" for values from QCTools docs
  
  -buff, --buffSize         | Size of the circular buffer. if user enters an even number it'll default to the next largest number to make it odd, default size 11
                        
  -te, --thumbExport        | export thumbnails on/ off, default off
  
  -ted, --thumbExportDelay  | minimum frames between exported thumbs, default 9000
                        
  -tep, --thumbExportPath   | Path to thumb export. if ommitted, uses the input base-path
                        
  -ds, --durationStart      | the duration in seconds to start analysis (ffmpeg equivalent -ss)
                        
  -de, --durationEnd        | the duration in seconds to stop analysis (ffmpeg equivalent -t)
                        
  -bd, --barsDetection      | bar detection on/ off, default off
  
  -pr, --print               | print over/under frame data to console window, default off
  
  -q, --quiet               | print ffmpeg output to console window, default off


##examples

###single tags

python qct-parse.py -t SATMAX -o 235 -t YMIN -u 16 -i /path/to/report.mkv.qctools.xml.gz

###run bars against default profile from QCTools docs

python qct-parse.py -bd -p default -i /path/to/reportsmkv.qctools.xml.gz

###print out thumbnails of frames beyond threshold

python qct-parse.py -p default -te -tep C:\path\to\export\folder -i C:\path\to\the\report.mkv.qctools.xml.gz

##some handy applescript to grep individual tags

###just percentages

python ./qct-parse.py -i input.mxf.qctools.xml.gz -bd -p lowTolerance | grep 'YMAX' | awk 'NR==1 {print $3}'

###total number of frame failures

python ./qct-parse.py -i input.mxf.qctools.xml.gz -bd -p lowTolerance | grep 'YMAX' | awk 'NR==1 {print $2}'

##dependencies

Python 2.7.x.

Requires that [lxml](http://lxml.de/) is installed on your system. For more info on how it's used, see [here](http://www.ibm.com/developerworks/library/x-hiperfparse/)

#makeqctoolsreport.py

##example

python makeqctoolsreport.py /path/to/input.mxf

##credits

@CoatesBrendan

@av_morgan
