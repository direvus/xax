# XAX

CD-ROM XA file extractor

## Details

Given a raw CDROM data track (.cdr) file, and a directory to extract into, XAX
will go through the track sector by sector and parse the headers.  XAX knows
how to parse Mode1, Mode2 and the CDROM XA Mode2/Form1 and Mode2/Form2 sectors.

It will then write the data contents of those sectors to files, grouped by
their "type", "file" and "channel" attributes.

The resulting filenames follow the format "type/file/channel", where "type" is
one of 'video', 'audio', 'data' or 'untyped', and "file" and "channel" are
two-digit hexadecimal numbers.  So, for example, all of the sectors for video
file 1, channel 31 will be written out to one continuous file at `video/01/1f`.

## Usage

`xax.py [-v] [-i INPUT_FILE] [-t TARGET_DIR]`

If you don't specify an input file, XAX will expect to receive the input on
stdin.  If you don't specify a target directory, XAX will output files in the
current working directory.

## Dependencies

All you need is a working Python 3 interpreter.  XAX uses only built-in Python
standard libraries.

## Installation

Copy xax.py onto your computer.

## License

XAX uses the "MIT" license, see the LICENSE file at the top level of the XAX
code repository.

## Author

XAX is written by Brendan Jurd.
