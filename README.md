# freeswitch-sounds-en-gb-richard
en-GB sounds for FreeSWITCH

Recorded by yours truly at 48kHz rather primitively (Macbook, mobile phone headset, quiet room, cloths, pillows & Audacity) but the results seem okay.
Let me know if you find any problems or want more sounds recorded.

Released in 48kHz, 32kHz, 16kHz and 8kHz as seems to be the norm.

### Tools
#### Transcription
To be able to record these files quickly, I wrote a script that uses Google Cloud Speech to transcribe the en-US callie FreeSWITCH sounds to a csv to be used as a script. The csv I used is also included. The transcription wasn't perfect so some of the transcriptions have been hand-modified.
The script also checks the en-CA files to see if it is included in that minimal set. The en-US set appears to be the most comprehensive, but I just needed the basics.
Note also that some of the en-CA files have slightly different names, also corrected in the csv.

#### Downsampling
There are also a set of scripts I wrote to help downsample the files using both Audacity and sox.
I recommend Audacity since it preserves the wav file tags.
