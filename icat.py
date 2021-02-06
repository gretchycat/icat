#!/usr/bin/python3
from PIL import Image
from optparse import OptionParser
import sys, math, os

def colordiff(c1, c2):  #compare how close two colors are
    return math.sqrt((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)

def term_24bit(c):
    r=int(c[0])
    g=int(c[1])
    b=int(c[2])
    return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+b0

def term_color(c):
    d=40
    gd=256/24
    r=int(max(0,c[0]-55)/40)
    g=int(max(0,c[1]-55)/40)
    b=int(max(0,c[2]-55)/40)
    rg=int(c[0]/gd)
    gg=int(c[1]/gd)
    bg=int(c[2]/gd)
    v=int((rg+gg+bg)/3)
    #is grey closer? or color
    dc=colordiff(c, (r*d, g*d, b*d))
    dg=colordiff(c, (v*gd, v*gd, v*gd))
    if (dg*3)<dc:
        return "\x1b[48;5;"+str(v+232)+"m"+b0
    return "\x1b[48;5;"+str(b+6*g+36*r+16)+"m"+b0

def term_grey(c):
    d=256/24
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    v=int((r+g+b)/3)
    return "\x1b[48;5;"+str(v+232)+"m"+b0

def term_16(c): #this is wrong.
    d=256/2
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    rg=int(c[0])
    gg=int(c[1])
    bg=int(c[2]) 
    v=int((rg+gg+bg)/3)
    c=r+2*g+4*b
    br=0
    if c==0 or c==7:
        if v<64:
            c=0
        if v>=64 and v<128:
            c=0
            br=1
        if v>=128 and v<192:
            c=7
        if v>=192:
            c=7
            br=1
    else:
        if v>127:
            br=1
    if br==1:
        return "\x1b[1;"+str(30+c)+"m"+b100
    else:
        return "\x1b[0;"+str(40+c)+"m"+b0

def term_8(c): 
    d=256/2
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return "\x1b["+str(40+r+2*g+4*b)+"m"+b0

def term_bw(c):
    r=int(c[0])
    g=int(c[1])
    b=int(c[2])
    v=(r+g+b)/3
    if v<51:
        return b0
    if v<102:
        return b25
    if v<153:
        return b50
    if v<204: 
        return b75
    else:
        return b100

def docat(imagefile, mode, forcew):
    rows,columns = os.popen('stty size', 'r').read().split()
    w=int(columns)
    img0 = Image.open(imagefile).convert(mode='RGB')
    resample=3
    if img0.width*2<w:
        w=img0.width*2
        resample=0
    if forcew>0:
        w=forcew
    h=int(w*img0.height/img0.width/2)
    img=img0.resize((w,h), resample=resample)
    img0.close()
    c0=0
    c1=0
    for y in range(h):
        for x in range(w):
            p=img.getpixel((x,y))
            if mode=='bw':
                c1=term_bw(p)
            if mode=='3bit':
                c1=term_8(p)
            if mode=='4bit':
                c1=term_16(p)
            if mode=='cga':
                c1=term_16(p)
            if mode=='8bit':
                c1=term_color(p)
            if mode=='grey':
                c1=term_grey(p)
            if mode=='24bit':
                c1=term_24bit(p)

            if (c0==c1):
                print(c1[-1],end='')
            else:
                print(c1,end='')
                c0=c1
        c0=0 
        print("\x1b[0m")
    img.close()

parser=OptionParser()
parser.add_option("-m", "--mode", dest="mode", default="24bit", 
        help="Display mode: 24bit | 8bit | grey | 4bit | 3bit | bw")
parser.add_option("-w", "--width", dest="width", default="0",
        help="0=auto, w>0 constrains image to the width")
(options, args)=parser.parse_args()

b0=' '
b25=u"\u2591"
b50=u"\u2592"
b75=u"\u2593"
b100=u"\u2588"

for imagefile in args:
    docat(imagefile, options.mode, int(options.width))
