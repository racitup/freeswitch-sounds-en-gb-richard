#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Uses Audacity to downsample Freeswitch sound files to the various rates required.
Takes a directory as input and expects files in the form:  .../lang/country/voice/app/rate/file.wav.
Outputs 8kHz, 16kHz and 32kHz versions in the current working dir: ./newrate/lang/country/voice/app/newrate/file.wav.
Quits if a file exists.
Make sure Audacity is running first and that mod-script-pipe is enabled in preferences before running this script.
"""

import os, sys, argparse, signal, json
from time import sleep
from contextlib import contextmanager


class Audacity:
    """Audacity interface class for running scripts, tested with Audacity 2.3.3"""
    def __init__(self):
        if sys.platform == 'win32':
            self.TONAME = '\\\\.\\pipe\\ToSrvPipe'
            self.FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
            self.EOL = '\r\n\0'
        else:
            self.TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
            self.FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
            self.EOL = '\n'
        signal.signal(signal.SIGALRM, self._alarm_handler)

        # When creating client, test connection to Audacity and also that there are no tracks loaded
        if len(self.track_info()) > 0:
            raise RuntimeError("Audacity already has tracks loaded. Please save what you are doing and close the tracks.")

    @contextmanager
    def _connection(self):
        # Set an alarm signal for 2secs in case Audacity is not responding/closed causing hang
        signal.alarm(2)
        try:
            with open(self.TONAME, 'w') as self.TOHANDLE, open(self.FROMNAME, 'rt') as self.FROMHANDLE:
                # Cancel alarm
                signal.alarm(0)
                yield
        except OSError as e:
            raise OSError("{}\nCheck that Audacity is running.".format(e))
        finally:
            del self.TOHANDLE, self.FROMHANDLE
            # Wait for Audacity to recover after closing
            sleep(0.1)

    def run_script(self, script):
        with self._connection():
            for cmd in script:
                self._command(cmd)

    def single_command(self, command):
        with self._connection():
            result = self._command(command)
        return result

    def track_info(self):
        """Returns loaded track info"""
        return json.loads(self.single_command("GetInfo: Type=Tracks Format=JSON"))

    def _alarm_handler(self, signum, frame):
        raise OSError("Audacity not responding.")

    def _command(self, command):
        """By default returns the finished status line"""
        # Set an alarm signal for 4secs in case Audacity is not responding/closed causing hang
        signal.alarm(4)

        # Write command
        self.TOHANDLE.write(command + self.EOL)
        self.TOHANDLE.flush()

        # Read response
        line = ''
        result = ''
        while 'BatchCommand finished:' not in line:
            result += line
            line = self.FROMHANDLE.readline()
        _, status = line.rsplit(sep=': ', maxsplit=1)
        print("Audacity {} [{}]".format(command, status.strip()))

        # Cancel alarm
        signal.alarm(0)

        return result


def split_path(path):
    "Splits freeswitch audio paths to individual params"
    info = {}
    for key in ["filename", "rate", "type", "voice", "country", "lang"]:
        path, info[key] = os.path.split(path)
    return info

def get_wavs(startpath):
    "Generator for wav files in directory"
    for root, dirs, files in os.walk(startpath, topdown=False):
        for name in files:
            if name.endswith(".wav"):
                yield os.path.abspath(os.path.join(root, name))

def direxists(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError("dir does not exist")

def newpath(wav, newrate):
    "Creates path to new file and ensures directory exists"
    info = split_path(wav)
    newwav = os.path.join(
        os.getcwd(),
        str(newrate),
        info["lang"],
        info["country"],
        info["voice"],
        info["type"],
        str(newrate),
        info["filename"]
    )
    if os.path.isfile(newwav):
        raise OSError("Output file already exists: {}".format(newwav))
    newpath, _ = os.path.split(newwav)
    os.makedirs(newpath, exist_ok=True)
    return newwav

def downsample(client, path, newrate):
    "Main downsample loop"
    for wav in get_wavs(path):
        newwav = newpath(wav, newrate)
        cutoff = (newrate * 7) / 16
        script = [
            'Import2: Filename="{}"'.format(wav), # Open, full file path required
            'SelectAll:', # Select All
            'Low-passFilter: frequency={} rolloff=dB48'.format(cutoff), # Lowpass filter @ max attenuation rolloff, repeat x5
            'Low-passFilter: frequency={} rolloff=dB48'.format(cutoff),
            'Low-passFilter: frequency={} rolloff=dB48'.format(cutoff),
            'Low-passFilter: frequency={} rolloff=dB48'.format(cutoff),
            'Low-passFilter: frequency={} rolloff=dB48'.format(cutoff),
            'SetProject: Rate={}'.format(newrate), # Resample to newrate
            'Export2: Filename="{}" NumChannels=1'.format(newwav), # Export to wav, full file path required
            'TrackClose:' # Close file
        ]
        client.run_script(script)
        #break

def main():
    """Main script"""
    parser = argparse.ArgumentParser(description=globals()["__doc__"])
    parser.add_argument("sounds", type=direxists)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    # Create interface to Audacity
    client = Audacity()

    # Run the test script
    if args.test:
        test(client, args)

    # Create the different versions
    downsample(client, args.sounds, 32000)
    downsample(client, args.sounds, 16000)
    downsample(client, args.sounds, 8000)

def play(client):
    """
    Macro that plays the currently loaded tracks.
    First has to get the length of the project to wait for playback to finish.
    """
    info = client.track_info()
    end = 0
    for track in info:
        end = max(end, track["end"])
    length = end - 0
    client.run_script(['CursProjectStart:', 'PlayStop:'])
    sleep(length)

def test(client, args):
    """Test script"""
    for wav in get_wavs(args.sounds):
        client.single_command('Import2: Filename="{}"'.format(wav))
        play(client)
        client.run_script(['SelectAll:', 'Low-passFilter: frequency=3500 rolloff=dB48'])
        play(client)
        client.single_command('TrackClose:')
        break
    sys.exit()

if __name__ == "__main__":
    main()
