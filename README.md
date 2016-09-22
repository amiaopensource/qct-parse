# qct-parse
scripts for parsing qctools reports

##arguments
  -h, --help            show this help message and exit
  -i I, --input I       the path to the input qctools.xml.gz file
  -t T, --tagname T     the tag name you want to test, e.g. SATMAX
  -o O, --over O        the threshold overage number
  -u U, --under U       the threshold under number
  -buff BUFF, --buffSize BUFF
                        Size of the circular buffer. if user enters an even
                        number it'll default to the next largest number to
                        make it odd (default size 11)
  -te, --thumbExport    export thumbnail
  -ted TED, --thumbExportDelay TED
                        minimum frames between exported thumbs
  -tep TEP, --thumbExportPath TEP
                        Path to thumb export. if ommitted, it uses the input
                        basename
  -ds DS, --durationStart DS
                        the duration in seconds to start analysis
  -de DE, --durationEnd DE
                        the duration in seconds to stop analysis
  -bd, --barsDetection  turns Bar Detection on and off
  -p, --print           print over/under frame data to console window
  -q, --quiet           print ffmpeg output to console window
