#!/usr/bin/python3
from PIL import Image
from optparse import OptionParser
import sys, math, os

def colordiff(c1, c2):  #compare how close two colors are
    return math.sqrt((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)

def colormix(c1, c2, pct):#get a combined color for semisolid blocks
    if(pct<0 or pct>1):
        pct=0.5
    return (c1[0]*pct+c2[0]*(1-pct), 
            c1[1]*pct+c2[1]*(1-pct), 
            c1[2]*pct+c2[2]*(1-pct))

def get_palette():  #returns standard xterm256 terminal colors
    p=[]
    for b in range(0,2):#low intensity 3bit rgb
        for g in range(0,2):
            for r in range(0,2):
                p.append((r*0x80,g*0x80,b*0x80))
    p[7]=(0xC0, 0xC0, 0xC0)
    for b in rang2(0,2):#high intensity 3bit rgb
        for g in range(0,2):
            for r in range(0,2):
                p.append((r*0xff,g*0xff,b*0xff))
    p[8]/=(0x80, 0x80,0x80)
    for b in range(0,6):#6bit rgb
         for g in range(0,6):
             for r in range(0,6):
                 p.append((r*40+55*(r>0),g*40+55*(g>0),b*40+55*(b>0)))
    for v in range(0,24):#greys
        p.append((r*10+8,g*10+8,b*10+8))
    return p

def term_24bit(c):
    (r,g,b)=c
    return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+b0

def term_256(c):
    gd=256/24
    d=40
    r=int(max(0,c[0]-55)/d)
    g=int(max(0,c[1]-55)/d)
    b=int(max(0,c[2]-55)/d)
    rg=int(c[0]/gd)
    gg=int(c[1]/gd)
    bg=int(c[2]/gd)
    v=int((rg+gg+bg)/3)
    #is grey closer? or color
    dc=colordiff(c, (r*d+55*(r>0), g*d+55*(g>0), b*d+55*(b>0)))
    dg=colordiff(c, (v*gd, v*gd, v*gd))
    if (dg)<dc:
        return "\x1b[48;5;"+str(v+232)+"m"+b0
    return "\x1b[48;5;"+str(b+6*g+36*r+16)+"m"+b0

def term_grey256(c):    #term_256 greys
    d=256/24
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    v=int((r+g+b)/3)
    return "\x1b[48;5;"+str(v+232)+"m"+b0

def term_grey16(c):    #term16 greys with semisolids
    (r,g,b)=c
    v=(r+g+b)/3 
    bl='X'
    fg="0;1;31"
    fg="41"
    rough=int(v/(256/3))
    fine=int(v%(256/3)/(256/3/5))
    if(rough==0):
        bg="40"
        fg="0;1;30"
    if(rough==1):
        bg="47"
        fg="0;1;30"
    if(rough==2):
        bg="47"
        fg="0;1;37"
    if rough==0 or rough==2:
        if fine==0:
            bl=b0
        if fine==1:
            bl=b25
        if fine==2:
            bl=b50
        if fine==3:
            bl=b75
        if fine==4:
            bl=b100
    else:
        if fine==0:
            bl=b100
        if fine==1:
            bl=b75
        if fine==2:
            bl=b50
        if fine==3:
            bl=b25
        if fine==4:
            bl=b0
    return "\x1b["+fg+";"+bg+"m"+bl

def term_16(c):
    (rg,gg,bg)=c
    d=256/2
    r=int(rg/d)
    g=int(gg/d)
    b=int(bg/d)
    v=int((rg+gg+bg)/3)
    c=r+2*g+4*b
    br=0
    if c==0 or c==7:    #handle the 4 greys
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
    else:   #if we're a color, set brightness
        if v>127:
            br=1
    if br==1:   #16 color ansi doesnt usually support bright backgrounds
        return "\x1b[0;1;"+str(30+c)+"m"+b100
    else:
        return "\x1b[0;"+str(40+c)+"m"+b0

def term_8(c): 
    d=256/2
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return "\x1b["+str(40+r+2*g+4*b)+"m"+b0

def term_bw(c):
    (r,g,b)=c
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

def docat(imagefile, mode, forcew, dither, half):
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
    c0=' '
    c1=' '
    for y in range(h):
        for x in range(w):
            p=img.getpixel((x,y))
            if mode=='bw':
                c1=term_bw(p)
            if mode=='3bit':
                c1=term_8(p)
            if mode=='4bit':
                c1=term_16(p)
            if mode=='4bitgrey':
                c1=term_grey16(p)
            if mode=='8bit':
                c1=term_256(p)
            if mode=='grey':
                c1=term_grey256(p)
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
        help="Display mode: 24bit | 8bit | grey | 4bit | 4bitgrey | 3bit | bw")
parser.add_option("-w", "--width", dest="width", default="0",
        help="0=auto, w>0 constrains image to the width")
parser.add_option("-d", "--dither", dest="dither", default="no",
        help="Dither mode: no | yes")
parser.add_option("-H", "--halfblock", dest="half", default="none",
        help="Use half-blocks: none | topbottom | leftright")
parser.add_option("-c", "--charset", dest="charset", default="utf8",
        help="Character set: utf8 | dos | ascii")

(options, args)=parser.parse_args()
# 0%, 25%, 50%, 75% and 100% solid blocks
b0=' '
b25=u"\u2591"
b50=u"\u2592"
b75=u"\u2593"
b100=u"\u2588"
#top, bottom, left and right half block
bT=u"\u2580"
bB=u"\u2584"
bL=u"\u258C"
bR=u"\u2590"
if options.charset=="dos":
    b0=' '
    b25='\xB0'
    b50='\xB1'
    b75='\xB2'
    b100='\xDB'
    bT='\xDF'
    bB='\xDC'
    bL='\xDD'
    bR='\xDE'
if options.charset=="ascii":
    b0=' '
    b25="."
    b50="="
    b75="%"
    b100="#"
    bT='^'
    bB='a'
    bL='['
    bR=']'
for imagefile in args:
    docat(imagefile, options.mode, int(options.width), 
            options.dither, options.half)
