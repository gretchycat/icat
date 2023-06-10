#!/usr/bin/python3
import os,sys
from optparse import OptionParser
from icat import ICat 
import urwid

parser=OptionParser(usage="usage: %prog [options] filelist")
parser.add_option("-m", "--mode", dest="mode", default="24bit", 
        help="Color mode: 24bit | 8bit | 8bitbright | 8bitgrey | 4bit | 4bitgrey | 3bit | bw")
parser.add_option("-f", "--fullblock", action="store_false", dest="full", default=True,
        help="Only use full blocks")
parser.add_option("-c", "--charset", dest="charset", default="utf8",
        help="Character set: utf8 | ascii")
(options, args)=parser.parse_args()

def showImage(image, x=0, y=0, f=True, w=30, h=15):
    ic=ICat(mode=options.mode.lower(), w=int(w), h=int(h), 
            zoom='aspect', f=options.full, charset=options.charset.lower(),
            x=int(x), y=int(y)) 
    ic.print(image)

def main():
    if len(args)==0:
        parser.print_help()
    else:
        showImage('sampleimage.jpg', x=10, y=5, w=30, h=15)

if __name__ == "__main__":
    main()

