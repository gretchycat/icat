#!/usr/bin/python3
import os,sys
from optparse import OptionParser
from icat import ICat 

def main():
    parser=OptionParser(usage="usage: %prog [options] filelist")
    parser.add_option("-m", "--mode", dest="mode", default="24bit", 
            help="Color mode: 24bit | 8bit | 8bitbright | 8bitgrey | 4bit | 4bitgrey | 3bit | bw")
    parser.add_option("-w", "--width", dest="width", default="0",
            help="0=auto, w>0 constrains image to the width")
    parser.add_option("-H", "--height", dest="height", default="0",
            help="0=auto, h>0 constrains image to the height")
    parser.add_option("-z", "--zoom", dest="zoom", default="aspect",
            help=" when w and h are constrained, zoom to aspect, fill, or stretch")
    parser.add_option("-f", "--fullblock", action="store_false", dest="full", default=True,
            help="Only use full blocks")
    parser.add_option("-b", "--browse", action="store_true", dest="browse", default=False,
            help="Show images in columns")
    parser.add_option("-B", "--B", dest="columns" , default="1", 
            help="number of columns in browse mode")
    parser.add_option("-c", "--charset", dest="charset", default="utf8",
            help="Character set: utf8 | ascii")
    parser.add_option("-x", '--x', dest="x", default="0", help="shift the image to X")
    parser.add_option("-y", '--y', dest="y", default="0", help="shift the image to Y")
    #ic=import icat.icat()
    (options, args)=parser.parse_args()
    if len(args)==0:
        parser.print_help()
    ic=ICat(mode=options.mode.lower(), w=int(options.width), h=int(options.height), 
            zoom=options.zoom, f=options.full, charset=options.charset.lower(),
            x=int(options.x), y=int(options.y), browse=options.browse)
    if options.browse:
        cols=3
        if int(options.columns)>1:
            cols=int(options.columns)
        i=0
        while i<len(args):
            il=()
            for c in range(0,cols):
                if i+c < len(args):
                    il=il+( args[i+c], )
                else:
                    il=il+("",)
            ic.print(il)
            i=i+cols
    else:
        for imagefile in args:
            ic.print(imagefile)

if __name__ == "__main__":
    main()

