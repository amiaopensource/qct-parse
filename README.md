# qct-parse
scripts for parsing qctools reports

##arguments
  -h, --help                | show this help message and exit

  -i, --input            | the path to the input qctools.xml.gz file
  
  -t, --tagname         | the tag name you want to test, e.g. SATMAX
  
  -o, --over             | the threshold overage number
  
  -u, --under             | the threshold under number
  
  -buff, --buffSize         | Size of the circular buffer. if user enters an even number it'll default to the next largest number to make it odd (default size 11)
                        
  -te, --thumbExport        | export thumbnails y/n
  
  -ted, --thumbExportDelay  | minimum frames between exported thumbs
                        
  -tep, --thumbExportPath   | Path to thumb export. if ommitted, it uses the input basename
                        
  -ds, --durationStart      | the duration in seconds to start analysis
                        
  -de, --durationEnd        | the duration in seconds to stop analysis
                        
  -bd, --barsDetection      | turns Bar Detection on and off
  
  -p, --print               | print over/under frame data to console window
  
  -q, --quiet               | print ffmpeg output to console window
