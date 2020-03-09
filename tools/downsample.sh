#!/bin/sh
# For downsampling freeswitch sound files to the various rates required, using sox
# Takes a file path as input and expects the form:  .../lang/country/voice/app/rate/file.wav
# Outputs 8kHz, 16kHz and 32kHz versions in:        ./newrate/lang/country/voice/app/newrate/file.wav

# NOTE: Sox does not preserve embedded file tags

orgpath=$1
fpath=$1

# Split the path
file=`basename "$fpath"`
fpath=`dirname "$fpath"`

rate=`basename "$fpath"`
fpath=`dirname "$fpath"`

app=`basename "$fpath"`
fpath=`dirname "$fpath"`

voice=`basename "$fpath"`
fpath=`dirname "$fpath"`

country=`basename "$fpath"`
fpath=`dirname "$fpath"`

lang=`basename "$fpath"`
fpath=`dirname "$fpath"`


function downsample {
  local newrate=$1
  local cutoff=$((newrate/2 - 250))

  # Create the new directory
  mkdir -p "./$newrate/$lang/$country/$voice/$app/$newrate"

  # Downsample the file
  sox "$orgpath" -b 16 -c 1 "./$newrate/$lang/$country/$voice/$app/$newrate/$file" sinc -$cutoff -t 250 rate $newrate
}

downsample 32000
downsample 16000
downsample 8000
