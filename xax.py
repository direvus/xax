#!/usr/bin/env python3
"""XAX: a file extractor for CD-ROM XA data

Usage: xax.py [-v] [-i INPUT_FILE] [-t TARGET_DIR]

Given a raw CDROM data track (*.cdr) file, and a directory to extract into, XAX
will go through the track sector by sector and parse their headers.  XAX knows
how to parse Mode1, Mode2 and the CDROM XA Mode2/Form1 and Mode2/Form2 sectors.

It will then write the data contents of those sectors to separate files,
grouped by their "type", "file" and "channel" attributes.

The resulting filenames follow the format "type/file/channel", where "type" is
one of 'video', 'audio', 'data' or 'untyped', and "file" and "channel" are
two-digit hexadecimal numbers.  So, for example, video file 1, channel 31 will
be written out to `video/01/1f`.

If you don't specify an input file, XAX will expect to receive the input on
stdin.  If you don't specify a target directory, XAX will output files in the
current working directory.
"""
import argparse
import os
import sys


SECTOR_SIZE = 2352
SYNC = b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'


def bcd_to_int(byte):
    return (byte & 15) + ((byte >> 4) * 10)


class Sector(object):
    def __init__(self, data):
        if len(data) != SECTOR_SIZE:
            raise ValueError(
                    f"Sector length is {len(data)}, expected {SECTOR_SIZE}.")
        if not data.startswith(SYNC):
            raise ValueError("Sector does not begin with the sync value.")
        self.minute = bcd_to_int(data[12])
        self.second = bcd_to_int(data[13])
        self.sector = bcd_to_int(data[14])
        self.mode = data[15]
        self.checksum = None
        self.ecc = None

        # CDROM XA Mode2 Form1/Form2 submode fields
        self.file = None
        self.channel = None
        self.submode = None
        self.codinginfo = None
        self.eor = None
        self.type_video = None
        self.type_audio = None
        self.type_data = None
        self.trigger = None
        self.form = None
        self.realtime = None
        self.eof = None

        if self.mode == 0:
            # Empty sector
            self.data_size = 0
            self.data = b''
        elif self.mode == 1:
            # Basic CDROM sector
            self.data_size = 2048
            self.data = data[16:2064]
            self.checksum = data[2064:2068]
            self.ecc = data[2076:]
        elif self.mode == 2:
            # CDROM XA Mode2
            subhead = data[16:20]
            self.file = subhead[0]
            self.channel = subhead[1] & 31
            self.submode = subhead[2]
            self.eor = bool(self.submode & 1)
            self.type_video = bool(self.submode & 2)
            self.type_audio = bool(self.submode & 4)
            self.type_data = bool(self.submode & 8)
            self.trigger = bool(self.submode & 16)
            if self.submode & 32:
                # Mode2/Form2
                self.form = 2
                self.data_size = 2324
                self.data = data[24:2348]
                self.checksum = data[2348:]
            else:
                # Mode2/Form1
                self.form = 1
                self.data_size = 2048
                self.data = data[24:2072]
                self.checksum = data[2072:2076]
                self.ecc = data[2076:]
            self.realtime = bool(self.submode & 64)
            self.eof = bool(self.submode & 128)
            self.codinginfo = subhead[3]
        else:
            raise ValueError("Unrecognised sector mode {self.mode}.")

    @property
    def is_filler(self):
        if self.mode == 0:
            return True

        if self.mode == 2 and self.form == 2 and self.submode == 32:
            return True

        return False

    def __str__(self):
        addr = f'{self.minute:02d}:{self.second:02d}:{self.sector:02d}'
        if self.mode == 0:
            mode = 'Empty'
        elif self.mode == 1:
            mode = 'Mode1'
        elif self.mode == 2:
            mode = 'Mode2'
            if self.form is not None:
                types = []
                if self.type_video:
                    types.append('Video')
                if self.type_audio:
                    types.append('Audio')
                if self.type_data:
                    types.append('Data')

                if types:
                    typelabel = '/'.join(types)
                else:
                    typelabel = 'None'

                mode += f'/Form{self.form} {typelabel} F{self.file:02x} C{self.channel:02x}'

        return f'{addr} {mode} [{self.data_size}]'


def main(infile, target_dir, verbose=False):
    os.makedirs(target_dir, exist_ok=True)
    n = 0
    while True:
        data = infile.read(SECTOR_SIZE)
        if data == b'':
            break
        sector = Sector(data)
        if verbose:
            print(f'{n:6d} {sector}')

        typename = 'untyped'
        if sector.type_video:
            typename = 'video'
        elif sector.type_audio:
            typename = 'audio'
        elif sector.type_data:
            typename = 'data'

        dirname = os.path.join(
                target_dir,
                typename,
                f'{sector.file:02x}')
        channel = f'{sector.channel:02x}'
        os.makedirs(dirname, exist_ok=True)
        path = os.path.join(dirname, channel)
        with open(path, 'ab') as fp:
            fp.write(sector.data)

        n += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory')
    parser.add_argument('-i', '--input-file')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    target_dir = '.'
    infile = sys.stdin.buffer

    if args.directory:
        target_dir = args.directory

    if args.input_file and args.input_file != '-':
        infile = open(args.input_file, 'rb')

    try:
        main(infile, target_dir, args.verbose)
    except BrokenPipeError:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print(err)
        sys.exit(1)
    finally:
        infile.close()
    sys.exit(0)
