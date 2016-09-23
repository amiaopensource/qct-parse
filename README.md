# qct-parse
scripts for parsing qctools reports

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
  
  -p, --print               | print over/under frame data to console window, default off
  
  -q, --quiet               | print ffmpeg output to console window, default off
