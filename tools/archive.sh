#!/bin/sh
# arg1: dir with wav files
# arg2: .tar.gz filename of archive
DIR=${1%/}
sudo chown -R 0:0 $DIR
find $DIR -name '*.wav' | GZIP=-9 tar -cvzf $2 -T -
md5 $2 > $2.md5
shasum -a 1 -p $2 > $2.sha1
shasum -a 256 -p $2 > $2.sha256
