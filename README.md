
# QCTools Automation Scripts

This repository contains scripts for automating analysis of QCTools reports.

## Overview

### Install from source:

* Create a new Python Virtual Environment for qct_parse
  * Unix based (Mac or Linux):    
    `python3 -m venv name_of_env` 
  * Windows:    
    `py -m venv name_of_env`
    (where 'name_of_env' is replaced with the name of your virtual environment) 
* Activate virtual env 
  * Unix based (Mac or Linux):     
    `source ./name_of_env/bin/activate`
  * Windows:     
    `name_of_env\scripts\activate`
* Install Package
  * Navigate to the repo root directory `path/to/qct-parse/`
  * Run the command:    
  `python -m pip install .`

### Test Code

If you intend to develop the code for your proposes or contribute to the open source project, a test directory is provided in the repo.
* Activate virtual env (see Install from source) 
* Install pytest 
  `pip install pytest`
* Run tests
  `python -m pytest`


### Commands:

- **`qct-parse`**  
  Finds frames that exceed thresholds for QCTool tag(s). Detect color bars with the `-bd` option.

---

# `qct-parse`

Run a single tag against a supplied value or multiple tags using a config file.

## Arguments

| Argument                   | Description                                                                                           |
|-----------------------------|-------------------------------------------------------------------------------------------------------|
| `-h`, `--help`              | Show this help message and exit                                                                       |
| `-i`, `--input`             | Path to the input `qctools.xml.gz` or `qctools.mkv` file                                              |
| `-t`, `--tagname`           | The tag name you want to test (e.g., `SATMAX`); see table of tag names below for list              |
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

## Tags

| Tag category                   | Tag names                                                                                           |
|-----------------------------|-------------------------------------------------------------------------------------------------------|
| [YUV values](https://bavc.github.io/qctools/filter_descriptions.html#yuv) | `YMIN,YLOW,YAVG,YHIGH,YMAX`<br>`UMIN,ULOW,UAVG,UHIGH,UMAX`<br>`VMIN,VLOW,VAVG,VHIGH,VMAX`   |
| [YUV values (difference)](https://bavc.github.io/qctools/filter_descriptions.html#diff)   | `YDIF,UDIF,VDIF`  |
| [Saturation values](https://bavc.github.io/qctools/filter_descriptions.html#saturation)   | `SATMIN,SATLOW,SATAVG,SATHIGH,SATMAX` |
| [Hue values](https://bavc.github.io/qctools/filter_descriptions.html#hue) | `HUEMED,HUEAVG` |
| [Temporal outliers](https://bavc.github.io/qctools/filter_descriptions.html#tout) | `TOUT`    |
| [Vertical line repetitions](https://bavc.github.io/qctools/filter_descriptions.html#vrep) | `VREP`   |
| [Broadcast range](https://bavc.github.io/qctools/filter_descriptions.html#brng) | `BRNG`    |
| [Mean square error fields](https://bavc.github.io/qctools/filter_descriptions.html#msef) | `mse_y,mse_u,mse_v,mse_avg`  |
| [Peak signal to noise ratio fields](https://bavc.github.io/qctools/filter_descriptions.html#psnrf) | `psnr_y,psnr_u,psnr_v,psnr_avg`   |

## Examples

### Run single tag tests
```bash
qct-parse -t SATMAX -o 235 -t YMIN -u 16 -i /path/to/report.mkv.qctools.xml.gz
```

### Run bars detection using default QCTools profile
```bash
qct-parse -bd -p default -i /path/to/report.mkv.qctools.mkv
```

### Export thumbnails of frames beyond threshold
```bash
qct-parse -p default -te -tep /path/to/export/folder -i /path/to/report.mkv.qctools.xml.gz
```

### Use peak values from detected color bars as thresholds
```bash
qct-parse -bd -be -i /path/to/report.mkv.qctools.xml.gz
```

## Input files

qct-parse.py will work with the following QCTools report formats: 
```
qctools.xml.gz 
qctools.mkv
```

If the qctools.xml.gz report is in an MKV attachment, the qctools.xml.gz report file will be extracted and saved as a separate file. 

Both 8-bit and 10-bit values are supported. The bit depth will be detected automatically, and does not need to be specified. 

## Config Files

If you wish to edit the profiles stored in the config.txt files, please note that there is a separate config.txt for 8-bit and 10-bit values.

In order to export thumbnails, the QCTools report must be in the same directory as the video file it is describing, and must have the same file name as the report (excluding the `qctools.xml.gz`).

## Logging

A log file is created with the same name as the input file but with a '.log' extension.
For example: `some_video_file.mkv.qctools.xml.gz.log`

Log files contain every instance of values over the specified threshold. For example:
`2024-10-03 17:02:35,737 SATMAX is over 181.02 with a value of 698.0 at duration 00:00:16.4500`

---

### Legacy Commands:

Not in active development. Please file an issue if you are interested in using these.

- **`makeqctoolsreport`**

A Python port of Morgan’s [makeqctoolsreport.as](https://github.com/iamdamosuzuki/QCToolsReport), this script generates QCTools `.xml.gz` reports from input video files.

## Example Usage
```bash
makeqctoolsreport /path/to/input.mxf
```

- **`overcatch`**

A script from the original qct-parse development for running a report against multiple profiles.

## Example Usage
```bash
overcatch /path/to/input.mxf
```

---

## Dependencies

Ensure Python 3.x.x is installed.

Requires FFmpeg.

This tool uses the `lxml` python module which is automatically installed with the qct-parse package. 

For more information on `lxml` usage, check out the [lxml documentation](http://lxml.de/).

---

## Contributors

- [@eddycolloton](https://github.com/eddycolloton)
- [@CoatesBrendan](https://github.com/CoatesBrendan)
- [@av_morgan](https://github.com/av_morgan)

## Maintainer

- [@av_morgan](https://github.com/av_morgan)
- [@eddycolloton](https://github.com/eddycolloton)
