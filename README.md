
# QCTools Automation Scripts

This repository contains scripts for automating common QCTools actions, such as parsing frame data for threshold violations and generating reports.

## Overview

### Scripts:

- **`qct-parse.py`**  
  Finds frames that exceed thresholds for saturation, luma, and more.
  
- **`makeqctoolsreport.py`**  
  Generates a QCTools `.xml.gz` report for a given input video file.

---

# `qct-parse.py`

Run a single tag against a supplied value or multiple tags using a config file (`qct-parse_config.txt`).

## Arguments

| Argument                   | Description                                                                                           |
|-----------------------------|-------------------------------------------------------------------------------------------------------|
| `-h`, `--help`              | Show this help message and exit                                                                       |
| `-i`, `--input`             | Path to the input `qctools.xml.gz` or `qctools.mkv` file                                              |
| `-t`, `--tagname`           | The tag name you want to test (e.g., `SATMAX`)                                                        |
| `-o`, `--over`              | Threshold overage number                                                                              |
| `-u`, `--under`             | Threshold under number                                                                                |
| `-p`, `--profile`           | Compare frame data against tag values from `config.txt`. Use `-p default` for QCTools default values  |
| `-buff`, `--buffSize`       | Circular buffer size. If even, defaults to the next odd number (default: 11)                          |
| `-te`, `--thumbExport`      | Enable/disable thumbnail export (default: off)                                                        |
| `-ted`, `--thumbExportDelay`| Minimum frames between exported thumbnails (default: 9000)                                             |
| `-tep`, `--thumbExportPath` | Path to thumbnail export. Uses input base-path if omitted                                             |
| `-ds`, `--durationStart`    | Start analysis from this time (seconds, equivalent to ffmpeg `-ss`)                                   |
| `-de`, `--durationEnd`      | End analysis after this time (seconds, equivalent to ffmpeg `-t`)                                     |
| `-bd`, `--barsDetection`    | Enable/disable bar detection (default: off)                                                           |
| `-be`, `--barsEvaluation`   | Use peak values from color bars as 'profile' if bars are detected                                      |
| `-pr`, `--print`            | Print over/under frame data to console (default: off)                                                 |
| `-q`, `--quiet`             | Suppress ffmpeg output in console (default: off)                                                      |

## Examples

### Run single tag tests
```bash
python qct-parse.py -t SATMAX -o 235 -t YMIN -u 16 -i /path/to/report.mkv.qctools.xml.gz
```

### Run bars detection using default QCTools profile
```bash
python qct-parse.py -bd -p default -i /path/to/report.mkv.qctools.mkv
```

### Export thumbnails of frames beyond threshold
```bash
python qct-parse.py -p default -te -tep /path/to/export/folder -i /path/to/report.mkv.qctools.xml.gz
```

## Input files

qct-parse.py will work with the following QCTools report formats: 
```
qctools.xml.gz 
qctools.mkv
```

If the qctools.xml.gz report is in an MKV attachment, the qctools.xml.gz report file will be extracted and saved as a separate file. 

In order to export thumbnails, the QCTools report must be in the same directory as the video file it is describing, and must have the same file name as the report (excluding the `qctools.xml.gz`).

## Logging

A log file is created with the same name as the input file but with a '.log' extension.
For example: `some_video_file.mkv.qctools.xml.gz.log`

Log files contain every instance of values over the specified threshold. For example:
`2024-10-03 17:02:35,737 SATMAX is over 181.02 with a value of 698.0 at duration 00:00:16.4500`

---

# `makeqctoolsreport.py`

A Python port of Morgan’s [makeqctoolsreport.as](https://github.com/iamdamosuzuki/QCToolsReport), this script generates QCTools `.xml.gz` reports from input video files.

## Example Usage
```bash
python makeqctoolsreport.py /path/to/input.mxf
```

---

## Dependencies

Ensure Python 3.x.x is installed.
Requires FFmpeg.

Additionally, install the `lxml` library:
```bash
pip install lxml
```

For more information on `lxml` usage, check out the [lxml documentation](http://lxml.de/).

---

## Contributors

- [@eddycolloton](https://github.com/eddycolloton)
- [@CoatesBrendan](https://github.com/CoatesBrendan)
- [@av_morgan](https://github.com/av_morgan)

## Maintainer

- [@av_morgan](https://github.com/av_morgan)
