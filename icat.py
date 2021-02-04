#!/usr/bin/python3
from PIL import Image
import sys
import math
import os
mode='24bit' #cga, 8bit, grey, 24bit

def colordiff(c1, c2):
    return math.sqrt((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)

def term_24bit(c):
    r=int(c[0])
    g=int(c[1])
    b=int(c[2])
    return "48;2;"+str(r)+";"+str(g)+";"+str(b) 

def term_color(c): #use greys too
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
        return "48;5;"+str(v+232)
    return "48;5;"+str(b+6*g+36*r+16)

def term_grey(c):
    d=256/24
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    v=int((r+g+b)/3)
    return "48;5;"+str(v+232)

def term_16(c): #this is wrong.
    d=256/2
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return str(40+r+2*g+4*b)

rows,columns = os.popen('stty size', 'r').read().split()
w=int(columns)
img0 = Image.open(sys.argv[1])
if img0.width*2<w:
    w=img0.width*2
h=int(w*img0.height/img0.width/2)
img=img0.resize((w,h))
img0.close()
c0=0
c1=0
for y in range(h):
    for x in range(w):
        p=img.getpixel((x,y))
        if mode=='cga':
            c1=term_16(p)
        if mode=='8bit':
            c1=term_color(p)
        if mode=='grey':
            c1=term_grey(p)
        if mode=='24bit':
            c1=term_24bit(p)
        if (c0==c1):
            print(" ",end='')
        else:
            print("\x1b["+c1+"m ",end='')
            c0=c1
    c0=0 
    print("\x1b[0m")
img.close()
