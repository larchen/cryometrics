# Cryometrics

Cryometrics is a command line utility for processing log files for
[Bluefors](https://bluefors.com/) and [Oxford](https://nanoscience.oxinst.com/) 
dilution refrigerators. It is primarily used as an input/processing daemon for 
[telegraf](https://www.influxdata.com/time-series-platform/telegraf/), but can 
also be used for one off conversions of the Oxford `.vcl` files.

## Installation

Clone the GitHub repository and install via pip.

```bash
git clone https://github.com/larchen/cryometrics.git

cd cryometrics
python -m pip install -e .
```

This will install the package as well as the command line script.

## Usage

To convert an Oxford log file to a human readable csv, run

```bash
# On Windows
cryometrics.exe oxford convert path/to/logfile.vcl > path/to/outfile.csv

# On OS X/Linux
cryometrics oxford convert path/to/logfile.vcl > path/to/outfile.csv
```

The script will output the converted logs to stdout, which can be redirected to
your file of choice.