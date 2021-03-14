#!/usr/bin/python3
import os,sys
from optparse import OptionParser
from icat import *

def main():
    parser=OptionParser(usage="usage: %prog [options] filelist")
    parser.add_option("-m", "--mode", dest="mode", default="24bit", 
            help="Color mode: 24bit | 8bit | 8bitgrey | 4bit | 4bitgrey | 3bit | bw")
    parser.add_option("-w", "--width", dest="width", default="0",
            help="0=auto, w>0 constrains image to the width")
    parser.add_option("-f", "--fullblock", action="store_false", dest="full", default=True,
            help="Only use full blocks")
    parser.add_option("-c", "--charset", dest="charset", default="utf8",
            help="Character set: utf8 | dos | ascii")
    parser.add_option("-x", '--x', dest="x", default="-1", help="shift the image to X")
    parser.add_option("-y", '--y', dest="y", default="-1", help="shift the image to Y")
    (options, args)=parser.parse_args()
    if len(args)==0:
        parser.print_help()
    for imagefile in args:
        docat(imagefile, options.mode.lower(), int(options.width), str(options.full).lower(), options.charset.lower(), int(options.x), int(options.y))

if __name__ == "__main__":
    main()

